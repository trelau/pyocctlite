from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "pyocctlite"
OUTPUT = ROOT / "docs" / "pyocctlite-api.md"

# Dunders that users call through syntax: iteration, len() and indexing
PUBLIC_DUNDERS = {"__iter__", "__len__", "__getitem__", "__contains__"}

Function = ast.FunctionDef | ast.AsyncFunctionDef


def internal_names(tree: ast.Module) -> set[str]:
    """
    Find the names that belong to the C++ layer: its imports and aliases or TypeVars built on them.

    :param ast.Module tree: Parsed module.
    :return: Names that must not appear in the public API.
    :rtype: set[str]
    """
    names = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "pyocctlite._occtlite":
            names.update(alias.asname or alias.name for alias in node.names)

    # module-level assignments in source order, so that one alias can build on another
    for node in tree.body:
        if isinstance(node, ast.Assign) and mentions(node.value, names):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def mentions(node: ast.AST | None, names: set[str]) -> bool:
    """
    Check if an expression refers to any of the given names.

    :param ast.AST | None node: Expression, if any.
    :param set[str] names: Names to look for.
    :return: True if any name is used.
    :rtype: bool
    """
    if node is None:
        return False
    return any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(node))


def is_public(name: str) -> bool:
    """
    Check if a member name is part of the public API.

    :param str name: Member name.
    :return: True if public.
    :rtype: bool
    """
    return not name.startswith("_") or name in PUBLIC_DUNDERS


def decorators(fn: Function) -> set[str]:
    """
    Get the decorator names of a function.

    :param Function fn: Function.
    :return: Decorator names, without any module prefix.
    :rtype: set[str]
    """
    found = set()
    for d in fn.decorator_list:
        if isinstance(d, ast.Name):
            found.add(d.id)
        elif isinstance(d, ast.Attribute):
            found.add(d.attr)
    return found


def format_arg(arg: ast.arg, default: ast.expr | None = None, prefix: str = "") -> str:
    """
    Format one parameter.

    :param ast.arg arg: Parameter.
    :param ast.expr | None default: Default value, if any.
    :param str prefix: Prefix for variadic parameters.
    :return: Parameter as source text.
    :rtype: str
    """
    text = prefix + arg.arg
    if arg.annotation is not None:
        text += f": {ast.unparse(arg.annotation)}"
    if default is not None:
        text += f" = {ast.unparse(default)}" if arg.annotation else f"={ast.unparse(default)}"
    return text


def format_args(args: ast.arguments, is_member: bool) -> str:
    """
    Format a parameter list, leaving out an unannotated ``self`` or ``cls``.

    :param ast.arguments args: Parameters.
    :param bool is_member: True if the first parameter may be ``self`` or ``cls``.
    :return: Parameters as source text.
    :rtype: str
    """
    positional = [*args.posonlyargs, *args.args]
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults))
    defaults += args.defaults

    parts = [format_arg(a, d) for a, d in zip(positional, defaults, strict=True)]
    if is_member and positional[0].annotation is None:
        parts = parts[1:]
    if args.posonlyargs:
        parts.insert(len(args.posonlyargs) - (len(positional) - len(parts)), "/")

    if args.vararg:
        parts.append(format_arg(args.vararg, prefix="*"))
    elif args.kwonlyargs:
        parts.append("*")
    parts += [format_arg(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults, strict=True)]
    if args.kwarg:
        parts.append(format_arg(args.kwarg, prefix="**"))
    return ", ".join(parts)


def signature_mentions(fn: Function, names: set[str]) -> bool:
    """
    Check if a function's parameters or return type refer to any of the given names.

    :param Function fn: Function.
    :param set[str] names: Names to look for.
    :return: True if any name is used.
    :rtype: bool
    """
    annotations = [fn.returns]
    args = fn.args
    for a in (*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg):
        if a is not None:
            annotations.append(a.annotation)
    return any(mentions(a, names) for a in annotations)


def format_bases(node: ast.ClassDef, internal: set[str]) -> str:
    """
    Format the bases of a class, leaving out the C++ layer.

    :param ast.ClassDef node: Class.
    :param set[str] internal: Names that belong to the C++ layer.
    :return: Bases in parentheses, or nothing if none are left.
    :rtype: str
    """
    bases = []
    for base in node.bases:
        if not mentions(base, internal):
            bases.append(ast.unparse(base))
        elif isinstance(base, ast.Subscript) and not mentions(base.value, internal):
            # ShapeTool[UniteIShapes] -> ShapeTool, and Generic[ToolT] -> nothing
            name = ast.unparse(base.value)
            if name != "Generic":
                bases.append(name)
    return f"({', '.join(bases)})" if bases else ""


def format_class(node: ast.ClassDef, internal: set[str]) -> list[str]:
    """
    Format a class and the members it defines.

    :param ast.ClassDef node: Class.
    :param set[str] internal: Names that belong to the C++ layer.
    :return: One line for the class and one for each public member.
    :rtype: list[str]
    """
    functions = [m for m in node.body if isinstance(m, Function)]
    overloaded = {f.name for f in functions if "overload" in decorators(f)}
    has_makers = any(f.name.startswith("by_") for f in functions)

    lines = [f"class {node.name}{format_bases(node, internal)}"]
    for member in node.body:
        # enum members
        if isinstance(member, ast.Assign):
            if any(isinstance(b, ast.Name) and b.id == "Enum" for b in node.bases):
                lines += [
                    f"    {node.name}.{t.id}" for t in member.targets if isinstance(t, ast.Name)
                ]
            continue
        if not isinstance(member, Function):
            continue

        name = member.name
        kinds = decorators(member)
        # overloads carry the result types, so the implementation adds nothing
        if name in overloaded and "overload" not in kinds:
            continue
        if signature_mentions(member, internal):
            continue

        returns = f" -> {ast.unparse(member.returns)}" if member.returns else ""
        if name == "__init__":
            if not has_makers:
                lines.append(f"    {node.name}({format_args(member.args, True)})")
        elif not is_public(name):
            continue
        elif kinds & {"property", "cached_property"}:
            annotation = ast.unparse(member.returns) if member.returns else "Any"
            lines.append(f"    .{name}: {annotation}")
        elif kinds & {"classmethod", "staticmethod"}:
            is_member = "classmethod" in kinds
            lines.append(f"    {node.name}.{name}({format_args(member.args, is_member)}){returns}")
        else:
            lines.append(f"    .{name}({format_args(member.args, True)}){returns}")
    return lines


def format_module(path: Path) -> str:
    """
    Format the public API of a module.

    :param Path path: Module file.
    :return: Heading and fenced signatures.
    :rtype: str
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    internal = internal_names(tree)

    # names re-exported from the C++ layer are public under their new names, like the errors
    exported: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            exported = ast.literal_eval(node.value)
    defined = {n.name for n in tree.body if isinstance(n, ast.ClassDef | ast.FunctionDef)}
    lines = [f"class {name}" for name in exported if name not in defined]
    internal -= set(exported)

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and is_public(node.name):
            lines += format_class(node, internal)
        elif isinstance(node, Function) and is_public(node.name):
            if signature_mentions(node, internal):
                continue
            returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            lines.append(f"{node.name}({format_args(node.args, False)}){returns}")

    body = "\n".join(lines)
    return f"# pyocctlite.{path.stem}\n\n```\n{body}\n```\n"


def main() -> None:
    """
    Write the API file, one section per public module in sorted order.
    """
    paths = sorted(p for p in PACKAGE.glob("*.py") if not p.name.startswith("_"))
    text = "\n".join(format_module(p) for p in paths)
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

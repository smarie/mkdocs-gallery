import ast
import codeop
import sys
from textwrap import dedent

import pytest

from mkdocs_gallery.gen_single import _needs_async_handling, _parse_code

SRC_FILE = __file__
COMPILER = codeop.Compile()
COMPILER_FLAGS = codeop.Compile().flags


needs_ast_unparse = pytest.mark.skipif(
    sys.version_info < (3, 9), reason="ast.unparse is only available for Python >= 3.9"
)


def test_non_async_syntax_error():
    with pytest.raises(SyntaxError, match="unexpected indent"):
        _parse_code("foo = None\n bar = None", src_file=SRC_FILE, compiler_flags=COMPILER_FLAGS)


@needs_ast_unparse
@pytest.mark.parametrize(
    ("code", "needs"),
    [
        pytest.param("None", False, id="no_async"),
        pytest.param(
            dedent(
                """
                async def afn():
                    return True

                import asyncio
                assert asyncio.run(afn())
                """
            ),
            False,
            id="asyncio_run",
        ),
        pytest.param(
            dedent(
                """
                async def afn():
                    return True
                
                assert await afn()
                """
            ),
            True,
            id="await",
        ),
        pytest.param(
            dedent(
                """
                async def agen():
                    yield True

                async for item in agen():
                    assert item
                """
            ),
            True,
            id="async_for",
        ),
        pytest.param(
            dedent(
                """
                async def agen():
                    yield True

                assert [item async for item in agen()] == [True]
                """
            ),
            True,
            id="async_comprehension",
        ),
        pytest.param(
            dedent(
                """
                import contextlib
                
                @contextlib.asynccontextmanager
                async def acm():
                    yield True

                async with acm() as ctx:
                    assert ctx
                """
            ),
            True,
            id="async_context_manager",
        ),
    ],
)
def test_async_handling(code, needs):
    assert _needs_async_handling(code, src_file=SRC_FILE, compiler_flags=COMPILER_FLAGS) is needs

    # Since AST objects are quite involved to compare, we unparse again and check that nothing has changed. Note that
    # since we are dealing with AST and not CST here, all whitespace is eliminated in the process and this needs to be
    # reflected in the input as well.
    code_stripped = "\n".join(line for line in code.splitlines() if line)
    code_unparsed = ast.unparse(_parse_code(code, src_file=SRC_FILE, compiler_flags=COMPILER_FLAGS))
    assert (code_unparsed == code_stripped) ^ needs

    if needs:
        assert not _needs_async_handling(code_unparsed, src_file=SRC_FILE, compiler_flags=COMPILER_FLAGS)

    exec(COMPILER(code_unparsed, SRC_FILE, "exec"), {})


@needs_ast_unparse
def test_async_handling_locals():
    sentinel = "sentinel"
    code = dedent(
        """
        async def afn():
            return True

        sentinel = {sentinel}
        
        assert await afn()
        """.format(
            sentinel=repr(sentinel)
        )
    )
    code_unparsed = ast.unparse(_parse_code(code, src_file=SRC_FILE, compiler_flags=COMPILER_FLAGS))

    locals = {}
    exec(COMPILER(code_unparsed, SRC_FILE, "exec"), locals)

    assert "sentinel" in locals and locals["sentinel"] == sentinel


@needs_ast_unparse
def test_async_handling_last_expression():
    code = dedent(
        """
        async def afn():
            return True

        result = await afn()
        assert result
        result
        """
    )

    code_unparsed_ast = _parse_code(code, src_file=SRC_FILE, compiler_flags=COMPILER_FLAGS)
    code_unparsed = ast.unparse(code_unparsed_ast)

    last = code_unparsed_ast.body[-1]
    assert isinstance(last, ast.Expr)

    locals = {}
    exec(COMPILER(code_unparsed, SRC_FILE, "exec"), locals)
    assert eval(ast.unparse(last.value), locals)

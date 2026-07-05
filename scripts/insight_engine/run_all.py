"""CLI entry point: ``python -m scripts.insight_engine.run_all``.

Thin shim around :func:`scripts.insight_engine.runner.run_all` so the
package can expose ``run_all`` as a plain function without a module/function
name collision.
"""

from scripts.insight_engine.runner import run_all

if __name__ == "__main__":
    run_all()

import os
import sublime
import sublime_plugin
from html import escape

# -------------------------
# LSP AVAILABILITY CHECK
# -------------------------
try:
    from LSP.plugin.core.registry import windows as lsp_windows
    from LSP.plugin.core.protocol import Request as LspRequest
    from LSP.plugin.core.views import text_document_identifier
    _LSP_AVAILABLE = True
except ImportError:
    print("[Breadcrumb] LSP package not found — symbol context unavailable.")
    _LSP_AVAILABLE = False


_context = []
_breadcrumb = ""


# -------------------------
# FILE PATH BREADCRUMB
# -------------------------
def format_breadcrumb(path):
    if not path:
        return "No file"
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    parts = [p for p in path.split(os.sep) if p]
    return " › ".join(parts[-5:])


# -------------------------
# SYMBOL HIERARCHY
# -------------------------
def find_symbol_path(symbols, line: int, path: list):
    for s in symbols:
        rng = s.get("range") or (s.get("location") or {}).get("range")
        if not rng:
            continue

        start = rng["start"]["line"]
        end = rng.get("end", rng["start"])["line"]

        if start <= line <= end:
            path.append(s.get("name", "?"))
            children = s.get("children", [])
            if children:
                find_symbol_path(children, line, path)
            break


# -------------------------
# SHOW POPUP
# -------------------------
def show_breadcrumb_popup(view, breadcrumb, context):
    context_html = "".join(f" › <em>{escape(c)}</em>" for c in context)
    html = f"""
    <body id="breadcrumb" style="margin:0;padding:0;">
        <div style="white-space:nowrap;padding:4px 8px;font-size:0.9rem;
                    background-color:var(--background);
                    border-bottom:1px solid color(var(--foreground) alpha(0.15));">
            📂 {escape(breadcrumb)}{context_html}
        </div>
    </body>
    """
    view.show_popup(
        html,
        location=view.visible_region().begin(),
        max_width=2000,
        flags=sublime.COOPERATE_WITH_AUTO_COMPLETE | sublime.HIDE_ON_MOUSE_MOVE_AWAY,
    )


# -------------------------
# COMMAND
# -------------------------
class BreadcrumbRefreshCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global _context, _breadcrumb
        view = self.view

        _breadcrumb = format_breadcrumb(view.file_name() or "")
        _context = []

        if not _LSP_AVAILABLE or not view.sel():
            show_breadcrumb_popup(view, _breadcrumb, _context)
            return

        cursor_row, _ = view.rowcol(view.sel()[0].begin())

        try:
            wm = lsp_windows.lookup(view.window())
            if not wm:
                show_breadcrumb_popup(view, _breadcrumb, _context)
                return

            sessions = list(wm.get_sessions())
            if not sessions:
                show_breadcrumb_popup(view, _breadcrumb, _context)
                return

            session = None
            for s in sessions:
                if s.has_capability("documentSymbolProvider"):
                    if s.config.selector and view.match_selector(0, s.config.selector):
                        session = s
                        break
                    session = s  # fallback

            if not session:
                show_breadcrumb_popup(view, _breadcrumb, _context)
                return

            def on_response(symbols):
                path = []
                if isinstance(symbols, list):
                    find_symbol_path(symbols, cursor_row, path)
                global _context
                _context = path
                sublime.set_timeout(
                    lambda: show_breadcrumb_popup(view, _breadcrumb, _context), 0
                )

            def on_error(err):
                print(f"[Breadcrumb] LSP error: {err}")
                sublime.set_timeout(
                    lambda: show_breadcrumb_popup(view, _breadcrumb, _context), 0
                )

            params = {"textDocument": text_document_identifier(view)}
            session.send_request(
                LspRequest.documentSymbols(params, view), on_response, on_error
            )

        except Exception as e:
            print(f"[Breadcrumb] Error: {e}")
            import traceback
            traceback.print_exc()
            show_breadcrumb_popup(view, _breadcrumb, _context)


# -------------------------
# EVENT LISTENER
# -------------------------
class BreadcrumbListener(sublime_plugin.EventListener):
    def _refresh(self, view):
        if (
            view
            and view.is_valid()
            and view.window()
            and view == view.window().active_view()
        ):
            view.run_command("breadcrumb_refresh")

    def on_activated_async(self, view):
        sublime.set_timeout(lambda: self._refresh(view), 100)

    def on_load_async(self, view):
        sublime.set_timeout(lambda: self._refresh(view), 100)

    def on_post_save_async(self, view):
        sublime.set_timeout(lambda: self._refresh(view), 100)

    def on_selection_modified_async(self, view):
        sublime.set_timeout(lambda: self._refresh(view), 100)


# -------------------------
# PLUGIN LIFECYCLE
# -------------------------
def plugin_loaded():
    print("[Breadcrumb] Plugin loaded" + ("" if _LSP_AVAILABLE else " (no LSP)"))

def plugin_unloaded():
    print("[Breadcrumb] Plugin unloaded")
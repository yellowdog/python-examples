"""
Unit tests for the _print_listing() / _print_flat() / _print_tree() formatting
functions in yd-ls.
"""

from types import SimpleNamespace
from unittest.mock import patch

from yellowdog_cli.ls import _find_base_prefix, _print_listing


def _listing(dirs=(), files=()):
    return SimpleNamespace(dirs=list(dirs), files=list(files))


def _dir(name: str, path: str | None = None):
    rpath = SimpleNamespace(path=path or name, name=name, size=0, mod_time=None)
    return SimpleNamespace(name=name, path=rpath)


def _file(
    name: str,
    path: str | None = None,
    size: int | None = None,
    mod_time: str | None = None,
):
    rpath = SimpleNamespace(path=path or name, name=name, size=size, mod_time=mod_time)
    return SimpleNamespace(name=name, path=rpath)


def _printed_lines(listing, recursive: bool = False) -> list[str]:
    """Return every string passed as the first positional arg to print_simple."""
    with patch("yellowdog_cli.ls.print_simple") as mock:
        _print_listing(listing, recursive=recursive)
    return [c.args[0] for c in mock.call_args_list]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestFindBasePrefix:
    def test_single_entry_nested(self):
        listing = _listing(files=[_file("f.txt", path="base/pfx/f.txt")])
        assert _find_base_prefix(listing) == "base/pfx"

    def test_common_prefix_of_siblings(self):
        listing = _listing(
            dirs=[_dir("a", "root/a"), _dir("b", "root/b")],
        )
        assert _find_base_prefix(listing) == "root"

    def test_mixed_depths_returns_listing_root(self):
        listing = _listing(
            dirs=[_dir("d", "root/d")],
            files=[_file("f.txt", "root/d/f.txt")],
        )
        assert _find_base_prefix(listing) == "root"

    def test_empty_listing(self):
        assert _find_base_prefix(_listing()) == ""

    def test_no_prefix(self):
        listing = _listing(files=[_file("f.txt", path="f.txt")])
        assert _find_base_prefix(listing) == ""


# ---------------------------------------------------------------------------
# Flat mode (non-recursive)
# ---------------------------------------------------------------------------


class TestPrintListingEmpty:
    def test_empty_listing_prints_empty_marker(self):
        with patch("yellowdog_cli.ls.print_simple") as mock:
            _print_listing(_listing())
        mock.assert_called_once_with("  (empty)")


class TestPrintListingFlatDirectories:
    def test_directory_name_has_slash_suffix(self):
        lines = _printed_lines(_listing(dirs=[_dir("mydir")]))
        assert any("mydir/" in line for line in lines)

    def test_directory_uses_DIR_label(self):
        lines = _printed_lines(_listing(dirs=[_dir("mydir")]))
        assert any("DIR" in line for line in lines)

    def test_multiple_directories(self):
        lines = _printed_lines(_listing(dirs=[_dir("alpha"), _dir("beta")]))
        assert any("alpha/" in line for line in lines)
        assert any("beta/" in line for line in lines)


class TestPrintListingFlatFiles:
    def test_filename_present_in_output(self):
        lines = _printed_lines(_listing(files=[_file("report.csv", size=512)]))
        assert any("report.csv" in line for line in lines)

    def test_size_formatted_with_commas(self):
        lines = _printed_lines(_listing(files=[_file("big.bin", size=1_234_567)]))
        assert any("1,234,567" in line for line in lines)

    def test_none_size_shows_empty_field(self):
        lines = _printed_lines(_listing(files=[_file("nosize.txt", size=None)]))
        assert any("nosize.txt" in line for line in lines)

    def test_mod_time_present_in_output(self):
        lines = _printed_lines(
            _listing(files=[_file("f.txt", size=10, mod_time="2024-01-15")])
        )
        assert any("2024-01-15" in line for line in lines)


class TestPrintListingFlatMixed:
    def test_dirs_appear_before_files(self):
        listing = _listing(dirs=[_dir("d")], files=[_file("f.txt", size=1)])
        lines = _printed_lines(listing)
        dir_idx = next(i for i, l in enumerate(lines) if "d/" in l)
        file_idx = next(i for i, l in enumerate(lines) if "f.txt" in l)
        assert dir_idx < file_idx

    def test_all_lines_indented(self):
        listing = _listing(
            dirs=[_dir("mydir")],
            files=[_file("file.txt", size=100), _file("long-name.bin", size=2_000_000)],
        )
        lines = _printed_lines(listing)
        assert all(line.startswith("  ") for line in lines)

    def test_override_quiet_set_on_all_lines(self):
        listing = _listing(files=[_file("f.txt", size=1)])
        with patch("yellowdog_cli.ls.print_simple") as mock:
            _print_listing(listing)
        for c in mock.call_args_list:
            assert c.kwargs.get("override_quiet") is True


# ---------------------------------------------------------------------------
# Tree mode (recursive)
# ---------------------------------------------------------------------------


def _tree_listing():
    """
    Simulate a recursive listing of base/pfx/:
      dir1/
        file_a.txt  (100 bytes)
        dir1a/
          file_b.txt  (200 bytes)
      file_root.txt  (50 bytes)
    """
    return _listing(
        dirs=[
            _dir("dir1", "base/pfx/dir1"),
            _dir("dir1a", "base/pfx/dir1/dir1a"),
        ],
        files=[
            _file("file_a.txt", "base/pfx/dir1/file_a.txt", size=100),
            _file("file_b.txt", "base/pfx/dir1/dir1a/file_b.txt", size=200),
            _file("file_root.txt", "base/pfx/file_root.txt", size=50),
        ],
    )


class TestPrintListingTree:
    def test_tree_contains_all_names(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        names = {"dir1", "dir1a", "file_a.txt", "file_b.txt", "file_root.txt"}
        for name in names:
            assert any(name in line for line in lines), f"Missing: {name}"

    def test_tree_dirs_have_slash_suffix(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        assert any("dir1/" in line for line in lines)
        assert any("dir1a/" in line for line in lines)

    def test_nested_dir_is_indented_more_than_parent(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        dir1_line = next(l for l in lines if "dir1/" in l and "dir1a" not in l)
        dir1a_line = next(l for l in lines if "dir1a/" in l)
        # Depth is indicated by the position of the ── connector in the line;
        # a child always has a deeper (higher-index) connector than its parent.
        assert dir1a_line.index("──") > dir1_line.index("──")

    def test_file_inside_nested_dir_is_most_indented(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        root_file_line = next(l for l in lines if "file_root.txt" in l)
        nested_file_line = next(l for l in lines if "file_b.txt" in l)
        assert nested_file_line.index("──") > root_file_line.index("──")

    def test_tree_uses_box_drawing_characters(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        joined = "\n".join(lines)
        assert "──" in joined

    def test_last_item_uses_corner_connector(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        # At least one line should use └──
        assert any("└──" in l for l in lines)

    def test_non_last_item_uses_branch_connector(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        # At least one line should use ├──
        assert any("├──" in l for l in lines)

    def test_file_size_appears_in_tree(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        assert any("100" in l for l in lines)

    def test_tree_dirs_before_files_at_each_level(self):
        lines = _printed_lines(_tree_listing(), recursive=True)
        # At root level: dir1 should appear before file_root.txt
        dir1_idx = next(
            i for i, l in enumerate(lines) if "dir1/" in l and "dir1a" not in l
        )
        root_file_idx = next(i for i, l in enumerate(lines) if "file_root.txt" in l)
        assert dir1_idx < root_file_idx

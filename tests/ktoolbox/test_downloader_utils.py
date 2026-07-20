from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from ktoolbox.configuration import config
from ktoolbox.downloader.utils import duplicate_file_check, filename_from_headers, parse_header, utime_from_headers


def test_header_parsing_and_filename_precedence() -> None:
    assert parse_header("attachment;filename=plain.txt;ignored=a=b") == {
        "attachment": None,
        "filename": "plain.txt",
    }
    assert filename_from_headers({}) is None
    assert filename_from_headers({"content-disposition": "attachment;filename=hello%20world.txt"}) == "hello world.txt"
    assert (
        filename_from_headers(
            {"Content-Disposition": "attachment;filename*=utf-8''preferred%2Etxt;filename=fallback.txt"}
        )
        == "preferred.txt"
    )
    assert (
        filename_from_headers({"Content-Disposition": "attachment;filename*=invalid;filename=fallback.txt"})
        == "fallback.txt"
    )
    assert filename_from_headers({"Content-Disposition": "attachment"}) is None


def test_duplicate_check_local_and_bucket(tmp_path: Path) -> None:
    local = tmp_path / "local" / "file.bin"
    local.parent.mkdir()
    assert duplicate_file_check(local) == (False, None)
    local.write_bytes(b"local")
    assert duplicate_file_check(local) == (True, "Download file already exists, skipping")

    config.downloader.use_bucket = True
    bucket = tmp_path / "bucket.bin"
    bucket.write_bytes(b"bucket")
    local.unlink()
    existed, message = duplicate_file_check(local, bucket)
    assert existed is True
    assert message == "Download file already exists in bucket, linking to local path"
    assert local.read_bytes() == b"bucket"
    assert os.stat(local).st_ino == os.stat(bucket).st_ino
    assert duplicate_file_check(local, bucket) == (
        True,
        "Download file already exists in both bucket and local, skipping",
    )


def test_utime_uses_http_dates_and_ignores_empty_headers(tmp_path: Path) -> None:
    path = tmp_path / "file"
    path.touch()
    with patch("ktoolbox.downloader.utils.os.utime") as mocked:
        assert utime_from_headers({}, path) is None
        mocked.assert_not_called()
        assert (
            utime_from_headers(
                {
                    "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
                    "Date": "Wed, 21 Oct 2015 08:28:00 GMT",
                },
                path,
            )
            is None
        )
    atime, mtime = mocked.call_args.args[1]
    assert atime == mtime == 1445412480.0

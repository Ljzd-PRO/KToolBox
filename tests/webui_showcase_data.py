from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShowcaseFile:
    name: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ShowcasePost:
    post_id: str
    title: str
    published: str
    added: str
    files: tuple[ShowcaseFile, ...] = ()


@dataclass(frozen=True, slots=True)
class ShowcaseCreator:
    service: str
    creator_id: str
    name: str
    indexed: str
    updated: str
    posts: tuple[ShowcasePost, ...]

    @property
    def key(self) -> str:
        return f"{self.service}:{self.creator_id}"


# Captured from Pawchive's public API on 2026-07-29. File sizes were read from
# HTTP response headers only. Bodies, media URLs, and all media bytes are
# intentionally excluded so the showcase remains deterministic and offline.
SHOWCASE_CREATORS = (
    ShowcaseCreator(
        service="fanbox",
        creator_id="476249",
        name="ミュー",
        indexed="2026-06-10T20:38:52.719107",
        updated="2026-07-28T06:28:34.927081",
        posts=(
            ShowcasePost(
                "12317073",
                "リク消化負け負けいろは",
                "2026-07-27T11:57:44",
                "2026-07-27T02:57:44",
                files=(
                    ShowcaseFile("Oeg5AiNkge3N7kDPHqve3zFR.jpeg", 9_000_601),
                    ShowcaseFile("DwUXXEf1yoEuxJ85IywLN130.jpeg", 8_845_956),
                    ShowcaseFile("rrpMSzw4JstcPoIYN1TKyIMC.jpeg", 8_849_519),
                    ShowcaseFile("I4Gi8JEmfm0A9ofcSSfFUfHZ.jpeg", 8_822_271),
                    ShowcaseFile("mM4G69OGO5OaSvNa9Y24W6lf.jpeg", 8_957_711),
                    ShowcaseFile("nUIk1qlF7wk45ncJc4h5PFts.jpeg", 8_940_231),
                ),
            ),
            ShowcasePost(
                "12301669",
                "らくがき",
                "2026-07-24T17:59:19",
                "2026-07-24T08:59:19",
                files=(
                    ShowcaseFile("cover.jpeg", 187_190),
                    ShowcaseFile("tf8yNr0YYrB43AktiGToRn9K.jpeg", 2_712_268),
                    ShowcaseFile("GgEyLNnnVHdmr4XB3DXEOyUj.jpeg", 3_111_863),
                ),
            ),
            ShowcasePost("12292527", "ミソラとイイコト9", "2026-07-22T20:30:44", "2026-07-22T11:30:44"),
            ShowcasePost("12282864", "しんちょーく！", "2026-07-20T23:01:23", "2026-07-20T14:01:23"),
            ShowcasePost("12260577", "ゆ", "2026-07-16T20:26:47", "2026-07-16T11:26:47"),
            ShowcasePost(
                "12248474",
                "いろはちゃんをRequestした方へ",
                "2026-07-14T12:54:27",
                "2026-07-14T03:54:27",
            ),
            ShowcasePost(
                "12245489",
                "ルイズマリーおちんぽすくわっと追加差分",
                "2026-07-13T20:35:02",
                "2026-07-13T11:35:02",
            ),
            ShowcasePost(
                "12240842",
                "ルイズマリーおちんぽすくわっと",
                "2026-07-12T21:36:28",
                "2026-07-12T12:36:28",
            ),
        ),
    ),
    ShowcaseCreator(
        service="fanbox",
        creator_id="6570768",
        name="haku3490",
        indexed="2026-06-10T05:07:44.272628",
        updated="2026-07-14T05:37:27.572646",
        posts=(
            ShowcasePost(
                "12202120",
                "竜華キサキ　手マン差分　",
                "2026-07-05T12:53:10",
                "2026-07-13T09:05:52.521423",
            ),
            ShowcasePost(
                "12141482",
                "轟はじめ　拘束イラマチオ差分",
                "2026-06-26T12:58:45",
                "2026-07-13T09:05:52.925236",
            ),
            ShowcasePost(
                "12103355",
                "轟はじめ　レOプ目＆ボーナス体位差分",
                "2026-06-19T13:00:00",
                "2026-07-13T09:05:53.365049",
            ),
            ShowcasePost(
                "11945182",
                "轟はじめ　トロ顔＆体に落書き差分",
                "2026-05-22T13:00:00",
                "2026-07-13T09:05:53.761256",
            ),
            ShowcasePost(
                "11886016",
                "轟はじめ　レOプ目＆裸差分",
                "2026-05-10T12:50:41",
                "2026-07-13T09:05:54.151095",
            ),
        ),
    ),
    ShowcaseCreator(
        service="fanbox",
        creator_id="6005584",
        name="mochirong",
        indexed="2026-06-10T05:08:22.691178",
        updated="2026-06-10T05:08:22.691178",
        posts=(
            ShowcasePost(
                "11104713",
                "Hanako🩷 (PSD + Process)",
                "2025-12-22T05:11:26",
                "2026-06-10T05:08:22.691178",
            ),
            ShowcasePost("10905790", "🖤🖤💙", "2025-11-15T06:03:46", "2026-06-10T05:08:22.691178"),
            ShowcasePost("10820656", "2020-2025", "2025-10-30T15:35:44", "2026-06-10T05:08:22.691178"),
            ShowcasePost(
                "10820063",
                "(⚠️必読 Important 필독⚠️) 今後の運営方針について…",
                "2025-10-30T15:35:12",
                "2026-06-10T05:08:22.691178",
            ),
            ShowcasePost("10819959", "Shimiko🧡", "2025-10-30T13:48:50", "2026-06-10T05:08:22.691178"),
        ),
    ),
)

SHOWCASE_CREATOR_BY_KEY = {creator.key: creator for creator in SHOWCASE_CREATORS}

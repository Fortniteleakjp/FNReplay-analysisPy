# fnreplayPy

Fortnite / Unreal Engine のリプレイファイル (`.replay`) を解析する Python ライブラリです。
C# 実装の [Shiqan/FortniteReplayDecompressor](https://github.com/Shiqan/FortniteReplayDecompressor) を Python へ移植しました。

外部ライブラリ無しで動作します (Oodle 展開・AES 復号とも純 Python 実装を同梱)。

## 特長

- リプレイのメタ情報・ヘッダー・イベント (撃破ログ、試合統計、チーム統計) の解析
- ネットワークストリーム (バンチ / プロパティ複製) の解析による、プレイヤー・武器・マップ情報の復元
- Oodle (Mermaid) 圧縮の展開を純 Python で実装。`oo2core` DLL があれば高速化も可能
- AES-256 ECB 復号。`cryptography` / `pycryptodome` があれば自動で利用、無ければ内蔵実装
- 解析の深さを `ParseMode` で切り替え可能 (速度と情報量のトレードオフ)
- CLI 付き (`python -m fnreplay`) — 概要表示と JSON 書き出し
- Unreal Engine 5.6 (エンジンネットワークバージョン 44) / Fortnite ビルド 41.x まで対応

## 動作環境

- Python 3.10 以上
- 依存ライブラリ: なし (任意で `cryptography`)

## インストール

Python 3.10 以上の環境で、リポジトリのルートから実行します。

```bash
python -m pip install .
```

開発中にソースの変更をすぐ反映したい場合は、編集可能インストールを使います。

```bash
python -m pip install -e ".[dev]"
```

`cryptography` を追加すると、暗号化されたリプレイの復号を高速化できます。

```bash
python -m pip install ".[crypto]"
```

開発用ツールと高速な復号を両方使う場合は、次のように指定できます。

```bash
python -m pip install -e ".[crypto,dev]"
```

### Windows で仮想環境を使う場合

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[crypto]"
```

PowerShell の実行ポリシーによって有効化できない場合は、仮想環境を有効化せずに
`.venv\Scripts\python.exe -m pip ...` のように実行してください。

## 使い方

### 最短手順

1. Fortnite などで保存した解析対象の `.replay` ファイルを用意します。
2. 上記の方法で `fnreplay` をインストールします。
3. リプレイのパスを指定して実行します。

```bash
python -m fnreplay path/to/match.replay
```

インストール済みのコマンドも使用できます。

```bash
fnreplay path/to/match.replay
```

既定の解析モードは `minimal` です。実行すると、リプレイ名・録画日時・プレイリスト・
プレイヤー数・撃破イベントなどの概要が標準出力に表示されます。

ファイルパスに空白が含まれる場合は、パス全体を引用符で囲みます。

```powershell
python -m fnreplay "C:\Replay Files\match.replay"
```

### ライブラリとして

```python
import fnreplay

replay = fnreplay.read_replay("match.replay")

print(replay.info.friendly_name)          # リプレイ名
print(replay.info.timestamp)              # 録画日時
print(replay.game_data.current_playlist)  # プレイリスト

for elimination in replay.eliminations:
    print(elimination.time, elimination.eliminator, "->", elimination.eliminated)

for player in replay.player_data:
    print(player.player_id, player.player_name, player.placement, player.kills)
```

`read_replay()` はファイルを読み込み、解析結果の `FortniteReplay` オブジェクトを返します。
パスには文字列のほか `pathlib.Path` も指定できます。

### 解析の深さを指定する

```python
from fnreplay import ParseMode, read_replay

# イベントだけ (最速)
replay = read_replay("match.replay", parse_mode=ParseMode.EventsOnly)

# プレイヤーの移動軌跡や武器・補給物資まで取得する
replay = read_replay("match.replay", parse_mode=ParseMode.Full)
for player in replay.player_data:
    for movement in player.locations:
        print(movement.replicated_world_time_seconds, movement.replicated_movement.location)
```

| モード | 内容 | 目安の速度 (12MB のリプレイ) |
| --- | --- | --- |
| `EventsOnly` | イベントチャンクのみ。撃破イベントや試合統計を短時間で取得したい場合 | 1 秒未満 |
| `Minimal` (既定) | `EventsOnly` + プレイヤー情報・ゲームステート | 3〜10 秒 |
| `Normal` | `Minimal` + 安全地帯などの通常のマップ情報 | 4〜11 秒 |
| `Full` | `Normal` + 移動軌跡・武器・補給物資・リブートバン | 6〜18 秒 |
| `Debug` | ほぼすべての型を解析。調査・デバッグ向け | 遅い |

プレイヤーの移動軌跡や武器などが必要な場合は `Full` を指定してください。
解析モードが低い場合、対象の属性は空のリストまたは `None` になります。
処理時間はファイルのサイズ・内容・実行環境によって変わるため、表の値は目安です。

### コマンドラインから

```bash
python -m fnreplay match.replay
```

```bash
python -m fnreplay match.replay --mode full --json result.json
```

`--json` を指定すると、解析結果全体を UTF-8 の JSON として保存します。列挙型は名前、
日時は ISO 8601 形式、バイト列は 16 進数文字列に変換されます。大量の移動データを扱う
場合は、JSON のサイズが大きくなるため `--mode minimal` や `--mode normal` から試してください。

主なオプション:

| オプション | 説明 |
| --- | --- |
| `--mode` | `events` / `minimal` / `normal` / `full` / `debug` |
| `--json PATH` | 解析結果を JSON として保存 |
| `--oodle [PATH]` | ネイティブ Oodle ライブラリを使用 (省略時は自動探索) |
| `-v`, `-vv` | ログレベルを上げる |

例えば、移動軌跡を解析して JSON に保存し、詳細ログも表示する場合は次のようにします。

```bash
python -m fnreplay match.replay --mode full --json result.json -vv
```

### ネイティブ Oodle で高速化する

`oo2core_*_win64.dll` (Fortnite のインストール先などに含まれる) を用意すると、展開処理をネイティブ実装に切り替えられます。

```python
import fnreplay

fnreplay.use_native_oodle()                       # 自動探索
fnreplay.use_native_oodle(r"C:\path\oo2core_9_win64.dll")  # パス指定
```

環境変数 `FNREPLAY_OODLE_LIBRARY` でもパスを指定できます。CLI では `--oodle` を付けた
ときにこの環境変数が参照されます。

```powershell
$env:FNREPLAY_OODLE_LIBRARY = "C:\path\oo2core_9_win64.dll"
python -m fnreplay match.replay --oodle
```

Python から使う場合は、環境変数を設定した後に `use_native_oodle()` を呼びます。

```python
import os
import fnreplay

os.environ["FNREPLAY_OODLE_LIBRARY"] = r"C:\path\oo2core_9_win64.dll"
if fnreplay.use_native_oodle():
    print("ネイティブ Oodle を使用します")
replay = fnreplay.read_replay("match.replay")
```

ライブラリが見つからない場合は `use_native_oodle()` が `False` を返し、純 Python 実装が
使われます。Oodle の DLL は本プロジェクトには含まれていないため、利用者自身で用意してください。

### エラーが出る場合

- `FileNotFoundError`: 指定した `.replay` のパスが正しいか確認してください。
- `InvalidReplayException`: Fortnite のリプレイファイルではない、またはファイルが壊れている可能性があります。
- Oodle の展開エラー: まずネイティブ Oodle を指定せずに試し、必要に応じて対応する `oo2core` DLL を `--oodle PATH` で指定してください。
- 解析が遅い: `--mode events` または `--mode minimal` を使い、必要な場合だけ `full` に上げてください。

## 取得できる主な情報

| 属性 | 内容 |
| --- | --- |
| `replay.info` | リプレイ名、録画日時、長さ、暗号化・圧縮の有無 |
| `replay.header` | エンジンバージョン、ブランチ、プラットフォーム |
| `replay.eliminations` | 撃破イベント (時刻・撃破者・被撃破者・座標・距離・ノックか) |
| `replay.stats` / `replay.team_stats` | 試合統計・チーム統計 |
| `replay.game_data` | セッション ID、プレイリスト、開始時刻、勝利チームなど |
| `replay.player_data` | プレイヤー ID、名前、チーム、順位、キル数、コスメ、移動軌跡 |
| `replay.team_data` | チーム構成と順位 |
| `replay.kill_feed` | ダウン・復活を含むキルフィード |
| `replay.map_data` | バトルバス、安全地帯、ラマ、補給物資、リブートバン |

## パッケージ構成

```
fnreplay/
├── unreal/              Unreal Engine 汎用のリプレイ解析
│   ├── archives.py        FArchive / BinaryReader / BitReader / NetBitReader
│   ├── replay_reader.py   チャンク・パケット・バンチ・プロパティの読み取り
│   ├── net_field_parser.py プロパティを Python オブジェクトへ変換
│   ├── export_registry.py  ネットフィールドエクスポートの宣言 API
│   ├── net_guid_cache.py   NetGUID とエクスポートグループの対応表
│   ├── models.py           FVector や FGameplayTag などの構造体
│   └── enums.py / paths.py / unreal_names.py / exceptions.py
├── fortnite/            Fortnite 固有の処理
│   ├── reader.py          イベント解析・復号・展開
│   ├── builder.py         受信データから解析結果を組み立てる
│   ├── models.py          PlayerData / GameData / MapData など
│   ├── events.py          撃破イベントや統計
│   └── exports/           ネットフィールドエクスポート定義
│       ├── generated.py     ジェネレーターによる自動生成 (146 クラス)
│       └── handwritten.py   独自のシリアライズを持つクラス
├── compression/         Oodle 展開 (kraken.py = 純 Python, oodle_native.py = ctypes)
├── crypto.py            AES-256 ECB 復号
└── cli.py               コマンドライン
```

### エクスポート定義の再生成

`fnreplay/fortnite/exports/generated.py` は C# の属性定義から自動生成しています。
本家が更新された場合は次のコマンドで再生成できます。

```bash
python tools/gen_exports.py <FortniteReplayDecompressor>/src/FortniteReplayReader/Models/NetFieldExports fnreplay/fortnite/exports/generated.py
```

## テスト

```bash
python -m pytest
```

C# 版のユニットテストのテストベクタを移植しています。実データを使うテストは環境変数で有効化します。

```bash
# Oodle 展開のテスト (OozSharp.Test/CompressedChunk を指定)
FNREPLAY_TEST_DATA=/path/to/CompressedChunk python -m pytest

# リプレイファイルを使ったエンドツーエンドのテスト
FNREPLAY_TEST_REPLAYS=/path/to/replays python -m pytest
```

## 本家 (C#) との違い

移植にあたり、次の点は意図的に挙動を変えています。

1. **量子化ベクトルの除算** — C# 版は型の昇格により整数除算になり小数が落ちますが、本実装は Unreal 本体と同じく実数で除算します (座標の精度が上がります)。
2. **`read_bits_to_int`** — C# 版は内部で 1 バイトに丸めるため 8 ビットを超える読み取りで上位ビットが落ちますが、本実装は全ビットを保持します。
3. **チャンネル切断時の通知** — C# 版はチャンネルを破棄した後にアクターを参照するため常に `null` になりますが、本実装は破棄前のアクターを渡します。
4. **撃破イベントの座標 (新しいリプレイ)** — エンジンバージョン 34 以降は transform が倍精度 (UE5 の LWC) になります。C# 版は 80 バイト読み飛ばして座標を捨てていますが、本実装は実際の値として解析します (消費バイト数は同じ)。
5. **`RepMovement` の回転量子化** — Fortnite ビルド 41.00 で、属性指定の無いアクター (PlayerPawn など) の回転量子化が 8 ビットから 16 ビットに拡大されました。`EngineNetworkVersion` は 40.x / 41.x とも 44 のままで判別できないため、リプレイのブランチ名と変更リスト番号から判定します ([FortniteReplayDecompressor#77](https://github.com/Shiqan/FortniteReplayDecompressor/pull/77) と同じ方式)。判定を誤った場合はもう一方の設定で読み直します。
6. **エンジンバージョン 37〜44** — Unreal Engine の `FEngineNetworkCustomVersion` に合わせて定義を追加し、次のバージョン差分に対応しました。
   - `FPredictionKey`: バージョン 34 以降は BaseKey が複製されない
   - `FGameplayAbilityRepAnimMontage`: バージョン 33 の `bIsMontage` / 37 の `PlayCount` に対応し、Position を UE と同じ float として読む (C# 版は圧縮整数として読んでいます)
   - `RemoteViewPitch16`: バージョン 42 で追加された 16 ビット版のプロパティ
   - プレイヤーコントローラーのチャンネルオープン: バージョン 41 の `ClientHandshakeId`、43 の `LocalPlayerConnectionIdentifier` を読み取る (本家 C# はこの 8 バイトを読まないため、以降のプロパティがすべてずれます)
7. **`CurrentPlaylistInfo`** — ビルド 41 以降は末尾にフィールドが追加されています。プレイリスト ID の位置は変わらないため ID はそのまま読み取り、残りは `extra_bits` として保持します。
8. **未対応部分** — 差分チェックポイント (delta checkpoints)、Mermaid モード 0、エントロピー符号化された Oodle サブストリームは本家と同じく未対応です。

## ライセンスについて

- 本ライブラリは MIT ライセンスの [FortniteReplayDecompressor](https://github.com/Shiqan/FortniteReplayDecompressor) (Copyright (c) 2020-2026 Shiqan) を基にしています。
- ただし `fnreplay/compression/kraken.py` は、GPLv3 で公開されている [powzix/ooz](https://github.com/powzix/ooz) を C# 経由で移植したものです。当該ファイルには GPL のコピーレフトが及ぶと考えられるため、配布形態を決める際はご注意ください (ネイティブ Oodle を使う場合は当該ファイルを取り除くこともできます)。
- Oodle 本体 (`oo2core_*.dll`) は Epic Games / RAD Game Tools の所有物であり、本リポジトリには含まれません。

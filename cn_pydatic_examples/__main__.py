"""非常簡單的命令列介面，用於輔助將範例程式碼複製到新目錄。

若要在原地運行範例，執行以下指令：

    uv run -m pydantic_ai_examples.<範例模組名稱>

例如：

    uv run -m pydantic_ai_examples.pydantic_model

若要將所有範例複製到新目錄，執行以下指令：

    uv run -m pydantic_ai_examples --copy-to <目的地路徑>

更多資訊請參考：https://ai.pydantic.dev/examples/
"""

import argparse
import sys
from pathlib import Path


def cli():
    # 獲取當前腳本所在目錄
    this_dir = Path(__file__).parent

    # 設定命令列解析器
    parser = argparse.ArgumentParser(
        prog='pydantic_ai_examples',
        description=__doc__,  # 使用模組文檔作為說明
        formatter_class=argparse.RawTextHelpFormatter,  # 保持說明文字的格式
    )
    # 添加版本選項
    parser.add_argument(
        '-v', '--version', action='store_true', help='顯示版本並退出'
    )
    # 添加複製到新目錄的選項
    parser.add_argument(
        '--copy-to', dest='DEST', help='將所有範例複製到新目錄'
    )

    # 解析命令列參數
    args = parser.parse_args()
    if args.version:
        # 匯入並顯示版本資訊
        from pydantic_ai import __version__

        print(f'pydantic_ai v{__version__}')
    elif args.DEST:
        # 如果指定了目標路徑，執行複製功能
        copy_to(this_dir, Path(args.DEST))
    else:
        # 如果沒有提供任何參數，顯示幫助資訊
        parser.print_help()


def copy_to(this_dir: Path, dst: Path):
    # 如果目標路徑已存在，則報錯並退出
    if dst.exists():
        print(f'錯誤：目標路徑 "{dst}" 已存在', file=sys.stderr)
        sys.exit(1)

    # 建立目標目錄及其父目錄
    dst.mkdir(parents=True)

    count = 0  # 計數器，用於統計複製的檔案數量
    # 遍歷當前目錄中的所有檔案
    for file in this_dir.glob('*.*'):
        # 開啟來源檔案以讀取，並將其內容寫入目標檔案
        with open(file, 'rb') as src_file:
            with open(dst / file.name, 'wb') as dst_file:
                dst_file.write(src_file.read())
        count += 1  # 更新計數器

    # 輸出複製完成的訊息
    print(f'已將 {count} 個範例檔案複製到 "{dst}"')


if __name__ == '__main__':
    # 如果腳本是直接執行的，則呼叫 cli 函數
    cli()

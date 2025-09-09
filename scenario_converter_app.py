"""
シナリオ自動変換AIソフトウェア - 統合UIアプリケーション
Streamlitを使用したWebインターフェース
"""

import streamlit as st
import os
import zipfile
import tempfile
from io import StringIO
from scenario_analyzer import ScenarioAnalyzer
from flowchart_generator import FlowchartGenerator
from datatable_generator import DataTableGenerator

def main():
    st.set_page_config(
        page_title="シナリオ自動変換AI",
        page_icon="🎮",
        layout="wide"
    )
    
    st.title("🎮 UE5シナリオ自動変換AIソフトウェア")
    st.markdown("---")
    
    # サイドバーで機能選択
    st.sidebar.title("機能選択")
    mode = st.sidebar.selectbox(
        "変換モードを選択してください",
        ["シナリオ変換", "サンプル実行", "使用方法"]
    )
    
    if mode == "シナリオ変換":
        scenario_conversion_mode()
    elif mode == "サンプル実行":
        sample_execution_mode()
    else:
        usage_instructions_mode()

def scenario_conversion_mode():
    st.header("📝 シナリオファイル変換")
    
    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "シナリオファイルをアップロードしてください",
        type=['txt', 'md'],
        help="テキストファイル(.txt)またはMarkdownファイル(.md)をアップロードしてください"
    )
    
    if uploaded_file is not None:
        # ファイル内容を読み込み
        scenario_text = str(uploaded_file.read(), "utf-8")
        
        # プレビュー表示
        st.subheader("📄 シナリオプレビュー")
        with st.expander("アップロードされたシナリオを表示", expanded=False):
            st.text_area("シナリオ内容", scenario_text, height=200, disabled=True)
        
        # 変換オプション
        st.subheader("⚙️ 変換オプション")
        col1, col2 = st.columns(2)
        
        with col1:
            generate_flowchart = st.checkbox("フローチャート生成", value=True)
        with col2:
            generate_datatable = st.checkbox("データテーブル生成", value=True)
        
        # 変換実行ボタン
        if st.button("🚀 変換実行", type="primary"):
            if not generate_flowchart and not generate_datatable:
                st.error("少なくとも一つの変換オプションを選択してください。")
                return
            
            with st.spinner("シナリオを解析中..."):
                try:
                    # シナリオ解析
                    analyzer = ScenarioAnalyzer()
                    scenario_structure = analyzer.analyze_scenario(scenario_text)
                    
                    st.success("✅ シナリオ解析が完了しました！")
                    
                    # 解析結果の表示
                    display_analysis_results(scenario_structure)
                    
                    # 変換実行
                    output_files = []
                    
                    if generate_flowchart:
                        with st.spinner("フローチャートを生成中..."):
                            flowchart_file = generate_flowchart_file(scenario_structure)
                            if flowchart_file:
                                output_files.append(flowchart_file)
                                st.success("✅ フローチャート生成完了")
                    
                    if generate_datatable:
                        with st.spinner("データテーブルを生成中..."):
                            datatable_files = generate_datatable_files(scenario_structure)
                            output_files.extend(datatable_files)
                            st.success("✅ データテーブル生成完了")
                    
                    # ダウンロードセクション
                    if output_files:
                        create_download_section(output_files)
                    
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {str(e)}")

def display_analysis_results(scenario_structure):
    """解析結果を表示"""
    st.subheader("📊 解析結果")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("シーン数", len(scenario_structure.scenes))
    with col2:
        st.metric("登場人物数", len(scenario_structure.characters))
    with col3:
        total_dialogues = sum(len(scene.dialogues) for scene in scenario_structure.scenes)
        st.metric("総セリフ数", total_dialogues)
    
    # 詳細情報
    with st.expander("詳細情報を表示"):
        st.write("**登場人物:**")
        for char in scenario_structure.characters:
            st.write(f"- {char.name}: {char.description}")
        
        st.write("**シーン一覧:**")
        for scene in scenario_structure.scenes:
            st.write(f"- {scene.title} (セリフ数: {len(scene.dialogues)}, 選択肢数: {len(scene.choices)})")

def generate_flowchart_file(scenario_structure):
    """フローチャートファイルを生成"""
    try:
        generator = FlowchartGenerator()
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.drawio', delete=False, encoding='utf-8')
        
        xml_content = generator.generate_flowchart(scenario_structure)
        temp_file.write(xml_content)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        st.error(f"フローチャート生成エラー: {str(e)}")
        return None

def generate_datatable_files(scenario_structure):
    """データテーブルファイルを生成"""
    try:
        generator = DataTableGenerator()
        tables = generator.generate_all_tables(scenario_structure)
        
        temp_files = []
        
        # 各テーブルをCSVファイルとして保存
        for table_name, table_data in tables.items():
            if table_data:
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
                
                import csv
                fieldnames = table_data[0].keys()
                writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(table_data)
                temp_file.close()
                
                # ファイル名を変更
                new_name = temp_file.name.replace('.csv', f'_{table_name}.csv')
                os.rename(temp_file.name, new_name)
                temp_files.append(new_name)
        
        # UE5構造体定義ファイルも生成
        struct_def = generator.generate_ue5_struct_definitions(scenario_structure)
        struct_file = tempfile.NamedTemporaryFile(mode='w', suffix='.h', delete=False, encoding='utf-8')
        struct_file.write(struct_def)
        struct_file.close()
        
        new_struct_name = struct_file.name.replace('.h', '_ScenarioDataStructs.h')
        os.rename(struct_file.name, new_struct_name)
        temp_files.append(new_struct_name)
        
        return temp_files
    except Exception as e:
        st.error(f"データテーブル生成エラー: {str(e)}")
        return []

def create_download_section(output_files):
    """ダウンロードセクションを作成"""
    st.subheader("📥 ダウンロード")
    
    # 個別ファイルダウンロード
    st.write("**個別ファイル:**")
    for file_path in output_files:
        filename = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        st.download_button(
            label=f"📄 {filename}",
            data=file_data,
            file_name=filename,
            mime="application/octet-stream"
        )
    
    # ZIPファイルダウンロード
    st.write("**一括ダウンロード:**")
    zip_data = create_zip_file(output_files)
    
    st.download_button(
        label="📦 全ファイルをZIPでダウンロード",
        data=zip_data,
        file_name="scenario_conversion_output.zip",
        mime="application/zip"
    )

def create_zip_file(file_paths):
    """複数ファイルをZIPにまとめる"""
    zip_buffer = StringIO()
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                zip_file.write(file_path, filename)
        
        temp_zip.seek(0)
        with open(temp_zip.name, 'rb') as f:
            return f.read()

def sample_execution_mode():
    """サンプル実行モード"""
    st.header("🎯 サンプル実行")
    
    sample_scenario = """【プロローグ】
主人公：こんにちは、私は冒険者です。
ナレーター：あなたは古い城の前に立っています。

1. 城に入る → 城内部
2. 引き返す → 村

【城内部】
主人公：暗くて怖いですね。
魔法使い：ようこそ、勇敢な冒険者よ。

1. 魔法使いと話す → 会話
2. 逃げる → プロローグ

【会話】
魔法使い：何か手伝えることはありますか？
主人公：この城について教えてください。
魔法使い：この城は古い秘密を隠しています。
"""
    
    st.subheader("📄 サンプルシナリオ")
    st.text_area("サンプル内容", sample_scenario, height=300, disabled=True)
    
    if st.button("🚀 サンプルを変換", type="primary"):
        with st.spinner("サンプルシナリオを変換中..."):
            try:
                # シナリオ解析
                analyzer = ScenarioAnalyzer()
                scenario_structure = analyzer.analyze_scenario(sample_scenario)
                
                st.success("✅ サンプル変換完了！")
                
                # 解析結果の表示
                display_analysis_results(scenario_structure)
                
                # ファイル生成
                output_files = []
                
                # フローチャート生成
                flowchart_file = generate_flowchart_file(scenario_structure)
                if flowchart_file:
                    output_files.append(flowchart_file)
                
                # データテーブル生成
                datatable_files = generate_datatable_files(scenario_structure)
                output_files.extend(datatable_files)
                
                # ダウンロードセクション
                if output_files:
                    create_download_section(output_files)
                
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")

def usage_instructions_mode():
    """使用方法モード"""
    st.header("📖 使用方法")
    
    st.markdown("""
    ## 🎮 UE5シナリオ自動変換AIソフトウェアについて
    
    このソフトウェアは、ゲーム開発者がテキスト形式で書いたシナリオを自動的に解析し、
    以下の形式に変換します：
    
    - **フローチャート**: draw.io形式（.drawio）
    - **データテーブル**: UE5用CSV形式
    
    ### 📝 シナリオの書き方
    
    #### 基本構造
    ```
    【シーン名】
    キャラクター名：セリフ内容
    
    1. 選択肢1 → 次のシーン名
    2. 選択肢2 → 次のシーン名
    ```
    
    #### 例
    ```
    【プロローグ】
    主人公：こんにちは、私は冒険者です。
    ナレーター：あなたは古い城の前に立っています。
    
    1. 城に入る → 城内部
    2. 引き返す → 村
    
    【城内部】
    主人公：暗くて怖いですね。
    魔法使い：ようこそ、勇敢な冒険者よ。
    ```
    
    ### 🔧 UE5での使用方法
    
    1. **構造体定義**: 生成された`ScenarioDataStructs.h`をUE5プロジェクトに追加
    2. **データテーブル作成**: UE5エディタでデータテーブルアセットを作成
    3. **CSVインポート**: 生成されたCSVファイルをデータテーブルにインポート
    4. **ブループリント**: データテーブルを参照してゲームロジックを実装
    
    ### 📊 生成されるファイル
    
    - `flowchart.drawio`: フローチャート（draw.io形式）
    - `DialogueTable.csv`: セリフデータ
    - `ChoiceTable.csv`: 選択肢データ
    - `SceneTable.csv`: シーンデータ
    - `CharacterTable.csv`: キャラクターデータ
    - `ScenarioDataStructs.h`: UE5用C++構造体定義
    
    ### 💡 Tips
    
    - シーン名は【】で囲んでください
    - キャラクター名とセリフは「：」で区切ってください
    - 選択肢は「数字. 選択肢テキスト → 次のシーン名」の形式で書いてください
    - ファイル形式は.txtまたは.mdに対応しています
    """)

if __name__ == "__main__":
    main()


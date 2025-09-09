"""
シナリオ解析AIモジュール
UE5ゲーム開発用のシナリオを解析し、構造化データを生成する
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import spacy
from openai import OpenAI

@dataclass
class Character:
    """登場人物クラス"""
    name: str
    description: str = ""

@dataclass
class DialogueLine:
    """セリフクラス"""
    character: str
    text: str
    emotion: Optional[str] = None

@dataclass
class Choice:
    """選択肢クラス"""
    text: str
    target_scene: str

@dataclass
class Scene:
    """シーンクラス"""
    id: str
    title: str
    description: str
    dialogues: List[DialogueLine]
    choices: List[Choice]
    next_scene: Optional[str] = None

@dataclass
class ScenarioStructure:
    """シナリオ構造クラス"""
    title: str
    characters: List[Character]
    scenes: List[Scene]

class ScenarioAnalyzer:
    """シナリオ解析クラス"""
    
    def __init__(self):
        # spaCyモデルの初期化（日本語）
        try:
            self.nlp = spacy.load("ja_core_news_sm")
        except OSError:
            print("日本語spaCyモデルが見つかりません。英語モデルを使用します。")
            self.nlp = spacy.load("en_core_web_sm")
        
        # OpenAI APIクライアントの初期化
        self.openai_client = OpenAI()
        
        # 正規表現パターン
        self.character_pattern = re.compile(r'^([^：:\n]+)[：:](.+)$', re.MULTILINE)
        self.scene_pattern = re.compile(r'^\s*【(.+?)】\s*$', re.MULTILINE)
        self.choice_pattern = re.compile(r'^\s*([1-9])\.\s*(.+?)(?:\s*→\s*(.+?))?$', re.MULTILINE)
    
    def analyze_scenario(self, scenario_text: str) -> ScenarioStructure:
        """
        シナリオテキストを解析し、構造化データを生成する
        
        Args:
            scenario_text: 解析対象のシナリオテキスト
            
        Returns:
            ScenarioStructure: 構造化されたシナリオデータ
        """
        # AIを使用してシナリオの基本構造を抽出
        basic_structure = self._extract_basic_structure_with_ai(scenario_text)
        
        # 登場人物の抽出
        characters = self._extract_characters(scenario_text, basic_structure)
        
        # シーンの抽出と解析
        scenes = self._extract_scenes(scenario_text, basic_structure)
        
        # タイトルの抽出
        title = basic_structure.get('title', 'Untitled Scenario')
        
        return ScenarioStructure(
            title=title,
            characters=characters,
            scenes=scenes
        )
    
    def _extract_basic_structure_with_ai(self, scenario_text: str) -> Dict[str, Any]:
        """
        OpenAI APIを使用してシナリオの基本構造を抽出
        """
        prompt = f"""
以下のシナリオテキストを解析し、以下の情報をJSON形式で抽出してください：

1. title: シナリオのタイトル
2. characters: 登場人物のリスト（名前と簡単な説明）
3. scenes: シーンのリスト（各シーンのID、タイトル、概要）
4. dialogue_format: セリフの記述形式（例：「キャラ名：セリフ」）
5. choice_format: 選択肢の記述形式（例：「1. 選択肢テキスト」）

シナリオテキスト：
{scenario_text[:2000]}...

JSONのみを返答してください。
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"AI解析でエラーが発生しました: {e}")
            # フォールバック：基本的な構造を返す
            return {
                "title": "Untitled Scenario",
                "characters": [],
                "scenes": [],
                "dialogue_format": "character:dialogue",
                "choice_format": "number.choice"
            }
    
    def _extract_characters(self, scenario_text: str, basic_structure: Dict) -> List[Character]:
        """登場人物を抽出"""
        characters = []
        
        # AIから取得した登場人物情報を使用
        ai_characters = basic_structure.get('characters', [])
        for char_info in ai_characters:
            if isinstance(char_info, dict):
                characters.append(Character(
                    name=char_info.get('name', ''),
                    description=char_info.get('description', '')
                ))
            elif isinstance(char_info, str):
                characters.append(Character(name=char_info))
        
        # 正規表現でも追加抽出
        dialogue_matches = self.character_pattern.findall(scenario_text)
        for char_name, _ in dialogue_matches:
            char_name = char_name.strip()
            if char_name and not any(c.name == char_name for c in characters):
                characters.append(Character(name=char_name))
        
        return characters
    
    def _extract_scenes(self, scenario_text: str, basic_structure: Dict) -> List[Scene]:
        """シーンを抽出"""
        scenes = []
        
        # シーン区切りを検出
        scene_matches = list(self.scene_pattern.finditer(scenario_text))
        
        if not scene_matches:
            # シーン区切りがない場合、全体を一つのシーンとして扱う
            scene = self._parse_scene_content("main", "メインシーン", scenario_text)
            scenes.append(scene)
        else:
            # 各シーンを解析
            for i, match in enumerate(scene_matches):
                scene_title = match.group(1)
                scene_id = f"scene_{i+1}"
                
                # シーンの内容を抽出
                start_pos = match.end()
                end_pos = scene_matches[i+1].start() if i+1 < len(scene_matches) else len(scenario_text)
                scene_content = scenario_text[start_pos:end_pos].strip()
                
                scene = self._parse_scene_content(scene_id, scene_title, scene_content)
                scenes.append(scene)
        
        return scenes
    
    def _parse_scene_content(self, scene_id: str, scene_title: str, content: str) -> Scene:
        """シーンの内容を解析"""
        dialogues = []
        choices = []
        
        # セリフを抽出
        dialogue_matches = self.character_pattern.findall(content)
        for char_name, dialogue_text in dialogue_matches:
            dialogues.append(DialogueLine(
                character=char_name.strip(),
                text=dialogue_text.strip()
            ))
        
        # 選択肢を抽出
        choice_matches = self.choice_pattern.findall(content)
        for choice_num, choice_text, target in choice_matches:
            choices.append(Choice(
                text=choice_text.strip(),
                target_scene=target.strip() if target else ""
            ))
        
        # シーンの説明を生成（セリフ以外のテキスト）
        description_text = content
        for match in self.character_pattern.finditer(content):
            description_text = description_text.replace(match.group(0), "")
        for match in self.choice_pattern.finditer(content):
            description_text = description_text.replace(match.group(0), "")
        
        description = " ".join(description_text.split())
        
        return Scene(
            id=scene_id,
            title=scene_title,
            description=description,
            dialogues=dialogues,
            choices=choices
        )
    
    def to_json(self, structure: ScenarioStructure) -> str:
        """構造化データをJSON形式で出力"""
        def serialize_dataclass(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return obj
        
        return json.dumps(structure, default=serialize_dataclass, ensure_ascii=False, indent=2)

# 使用例
if __name__ == "__main__":
    # サンプルシナリオ
    sample_scenario = """
【プロローグ】
主人公：こんにちは、私は冒険者です。
ナレーター：あなたは古い城の前に立っています。

1. 城に入る → 城内部
2. 引き返す → 村

【城内部】
主人公：暗くて怖いですね。
魔法使い：ようこそ、勇敢な冒険者よ。

1. 魔法使いと話す → 会話
2. 逃げる → プロローグ
"""
    
    analyzer = ScenarioAnalyzer()
    result = analyzer.analyze_scenario(sample_scenario)
    print(analyzer.to_json(result))


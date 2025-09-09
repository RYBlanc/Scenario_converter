"""
UE5データテーブル生成モジュール
シナリオ構造からUE5で使用可能なCSVデータテーブルを生成する
"""

import csv
from typing import List, Dict, Any
from scenario_analyzer import ScenarioStructure, Scene, DialogueLine, Choice
from dataclasses import dataclass

@dataclass
class DialogueTableRow:
    """セリフテーブルの行データ"""
    ID: str
    SceneID: str
    SceneName: str
    CharacterName: str
    DialogueText: str
    EmotionTag: str
    NextDialogueID: str
    HasChoices: bool
    ChoiceCount: int

@dataclass
class ChoiceTableRow:
    """選択肢テーブルの行データ"""
    ID: str
    DialogueID: str
    ChoiceText: str
    TargetSceneID: str
    TargetSceneName: str
    ChoiceIndex: int

@dataclass
class SceneTableRow:
    """シーンテーブルの行データ"""
    ID: str
    SceneName: str
    Description: str
    FirstDialogueID: str
    DialogueCount: int
    HasChoices: bool
    IsEndScene: bool

@dataclass
class CharacterTableRow:
    """キャラクターテーブルの行データ"""
    ID: str
    CharacterName: str
    Description: str
    DialogueCount: int

class DataTableGenerator:
    """UE5データテーブル生成クラス"""
    
    def __init__(self):
        self.dialogue_counter = 1
        self.choice_counter = 1
        self.scene_counter = 1
        self.character_counter = 1
    
    def generate_all_tables(self, scenario: ScenarioStructure) -> Dict[str, List[Dict]]:
        """
        シナリオ構造から全てのデータテーブルを生成
        
        Args:
            scenario: 解析されたシナリオ構造
            
        Returns:
            Dict[str, List[Dict]]: テーブル名をキーとした辞書
        """
        # 各テーブルを生成
        dialogue_table = self._generate_dialogue_table(scenario)
        choice_table = self._generate_choice_table(scenario)
        scene_table = self._generate_scene_table(scenario)
        character_table = self._generate_character_table(scenario)
        
        return {
            "DialogueTable": dialogue_table,
            "ChoiceTable": choice_table,
            "SceneTable": scene_table,
            "CharacterTable": character_table
        }
    
    def _generate_dialogue_table(self, scenario: ScenarioStructure) -> List[Dict]:
        """セリフテーブルを生成"""
        dialogue_rows = []
        
        for scene in scenario.scenes:
            for i, dialogue in enumerate(scene.dialogues):
                dialogue_id = f"DLG_{self.dialogue_counter:04d}"
                next_dialogue_id = ""
                
                # 次のセリフIDを設定
                if i + 1 < len(scene.dialogues):
                    next_dialogue_id = f"DLG_{self.dialogue_counter + 1:04d}"
                
                row = DialogueTableRow(
                    ID=dialogue_id,
                    SceneID=scene.id,
                    SceneName=scene.title,
                    CharacterName=dialogue.character,
                    DialogueText=dialogue.text,
                    EmotionTag=dialogue.emotion or "Normal",
                    NextDialogueID=next_dialogue_id,
                    HasChoices=len(scene.choices) > 0 and i == len(scene.dialogues) - 1,
                    ChoiceCount=len(scene.choices) if i == len(scene.dialogues) - 1 else 0
                )
                
                dialogue_rows.append(row.__dict__)
                self.dialogue_counter += 1
        
        return dialogue_rows
    
    def _generate_choice_table(self, scenario: ScenarioStructure) -> List[Dict]:
        """選択肢テーブルを生成"""
        choice_rows = []
        dialogue_id_map = self._create_dialogue_id_map(scenario)
        
        for scene in scenario.scenes:
            if scene.choices:
                # 最後のセリフのIDを取得
                last_dialogue_id = dialogue_id_map.get((scene.id, len(scene.dialogues) - 1), "")
                
                for i, choice in enumerate(scene.choices):
                    choice_id = f"CHC_{self.choice_counter:04d}"
                    
                    # ターゲットシーンの情報を取得
                    target_scene = next((s for s in scenario.scenes if s.title == choice.target_scene), None)
                    target_scene_id = target_scene.id if target_scene else ""
                    target_scene_name = target_scene.title if target_scene else choice.target_scene
                    
                    row = ChoiceTableRow(
                        ID=choice_id,
                        DialogueID=last_dialogue_id,
                        ChoiceText=choice.text,
                        TargetSceneID=target_scene_id,
                        TargetSceneName=target_scene_name,
                        ChoiceIndex=i + 1
                    )
                    
                    choice_rows.append(row.__dict__)
                    self.choice_counter += 1
        
        return choice_rows
    
    def _generate_scene_table(self, scenario: ScenarioStructure) -> List[Dict]:
        """シーンテーブルを生成"""
        scene_rows = []
        dialogue_id_map = self._create_dialogue_id_map(scenario)
        
        for scene in scenario.scenes:
            first_dialogue_id = dialogue_id_map.get((scene.id, 0), "")
            is_end_scene = len(scene.choices) == 0 and not scene.next_scene
            
            row = SceneTableRow(
                ID=scene.id,
                SceneName=scene.title,
                Description=scene.description,
                FirstDialogueID=first_dialogue_id,
                DialogueCount=len(scene.dialogues),
                HasChoices=len(scene.choices) > 0,
                IsEndScene=is_end_scene
            )
            
            scene_rows.append(row.__dict__)
        
        return scene_rows
    
    def _generate_character_table(self, scenario: ScenarioStructure) -> List[Dict]:
        """キャラクターテーブルを生成"""
        character_rows = []
        character_dialogue_count = {}
        
        # 各キャラクターのセリフ数をカウント
        for scene in scenario.scenes:
            for dialogue in scene.dialogues:
                char_name = dialogue.character
                character_dialogue_count[char_name] = character_dialogue_count.get(char_name, 0) + 1
        
        # キャラクターテーブルを生成
        for character in scenario.characters:
            char_id = f"CHAR_{self.character_counter:04d}"
            dialogue_count = character_dialogue_count.get(character.name, 0)
            
            row = CharacterTableRow(
                ID=char_id,
                CharacterName=character.name,
                Description=character.description,
                DialogueCount=dialogue_count
            )
            
            character_rows.append(row.__dict__)
            self.character_counter += 1
        
        return character_rows
    
    def _create_dialogue_id_map(self, scenario: ScenarioStructure) -> Dict[tuple, str]:
        """シーンとセリフインデックスからセリフIDへのマッピングを作成"""
        dialogue_id_map = {}
        dialogue_counter = 1
        
        for scene in scenario.scenes:
            for i, dialogue in enumerate(scene.dialogues):
                dialogue_id = f"DLG_{dialogue_counter:04d}"
                dialogue_id_map[(scene.id, i)] = dialogue_id
                dialogue_counter += 1
        
        return dialogue_id_map
    
    def save_tables_to_csv(self, scenario: ScenarioStructure, output_dir: str = "."):
        """全てのテーブルをCSVファイルとして保存"""
        tables = self.generate_all_tables(scenario)
        
        for table_name, table_data in tables.items():
            if table_data:  # データが存在する場合のみ保存
                filename = f"{output_dir}/{table_name}.csv"
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = table_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    writer.writerows(table_data)
                
                print(f"{table_name} を {filename} に保存しました。")
    
    def generate_ue5_struct_definitions(self, scenario: ScenarioStructure) -> str:
        """UE5で使用するC++構造体定義を生成"""
        struct_definitions = """
// UE5用データテーブル構造体定義
// これらの構造体をC++で定義し、対応するデータテーブルアセットを作成してください

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "ScenarioDataStructs.generated.h"

// セリフデータ構造体
USTRUCT(BlueprintType)
struct YOURGAME_API FDialogueTableRow : public FTableRowBase
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString SceneID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString SceneName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString CharacterName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString DialogueText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString EmotionTag;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString NextDialogueID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    bool HasChoices;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    int32 ChoiceCount;
};

// 選択肢データ構造体
USTRUCT(BlueprintType)
struct YOURGAME_API FChoiceTableRow : public FTableRowBase
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Choice")
    FString DialogueID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Choice")
    FString ChoiceText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Choice")
    FString TargetSceneID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Choice")
    FString TargetSceneName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Choice")
    int32 ChoiceIndex;
};

// シーンデータ構造体
USTRUCT(BlueprintType)
struct YOURGAME_API FSceneTableRow : public FTableRowBase
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Scene")
    FString SceneName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Scene")
    FString Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Scene")
    FString FirstDialogueID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Scene")
    int32 DialogueCount;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Scene")
    bool HasChoices;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Scene")
    bool IsEndScene;
};

// キャラクターデータ構造体
USTRUCT(BlueprintType)
struct YOURGAME_API FCharacterTableRow : public FTableRowBase
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Character")
    FString CharacterName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Character")
    FString Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Character")
    int32 DialogueCount;
};
"""
        return struct_definitions

# 使用例
if __name__ == "__main__":
    from scenario_analyzer import ScenarioAnalyzer
    
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
    
    # シナリオを解析
    analyzer = ScenarioAnalyzer()
    scenario_structure = analyzer.analyze_scenario(sample_scenario)
    
    # データテーブルを生成
    generator = DataTableGenerator()
    generator.save_tables_to_csv(scenario_structure)
    
    # UE5構造体定義を保存
    struct_def = generator.generate_ue5_struct_definitions(scenario_structure)
    with open("ScenarioDataStructs.h", "w", encoding="utf-8") as f:
        f.write(struct_def)
    print("UE5構造体定義を ScenarioDataStructs.h に保存しました。")


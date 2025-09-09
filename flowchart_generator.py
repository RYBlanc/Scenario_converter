"""
フローチャート生成モジュール
シナリオ構造からdraw.io形式のXMLフローチャートを生成する
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from scenario_analyzer import ScenarioStructure, Scene, Choice
import uuid

class FlowchartGenerator:
    """フローチャート生成クラス"""
    
    def __init__(self):
        self.node_width = 120
        self.node_height = 60
        self.choice_width = 100
        self.choice_height = 40
        self.spacing_x = 200
        self.spacing_y = 150
        self.start_x = 100
        self.start_y = 100
        
    def generate_flowchart(self, scenario: ScenarioStructure) -> str:
        """
        シナリオ構造からdraw.io形式のXMLフローチャートを生成
        
        Args:
            scenario: 解析されたシナリオ構造
            
        Returns:
            str: draw.io形式のXMLファイル内容
        """
        # mxGraphModelのルート要素を作成
        mxgraph_model = ET.Element("mxGraphModel")
        root = ET.SubElement(mxgraph_model, "root")
        
        # デフォルトのセルを追加
        default_cell_0 = ET.SubElement(root, "mxCell", id="0")
        default_cell_1 = ET.SubElement(root, "mxCell", id="1", parent="0")
        
        # ノードの位置を計算
        node_positions = self._calculate_positions(scenario.scenes)
        
        # 各シーンをノードとして追加
        cell_id = 2
        scene_to_id = {}
        
        for i, scene in enumerate(scenario.scenes):
            x, y = node_positions[scene.id]
            
            # シーンノードを作成
            scene_cell = ET.SubElement(root, "mxCell", 
                                     id=str(cell_id),
                                     value=self._format_scene_text(scene),
                                     style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;",
                                     vertex="1",
                                     parent="1")
            
            geometry = ET.SubElement(scene_cell, "mxGeometry",
                                   x=str(x), y=str(y),
                                   width=str(self.node_width),
                                   height=str(self.node_height),
                                   as_="geometry")
            
            scene_to_id[scene.id] = cell_id
            cell_id += 1
            
            # 選択肢がある場合、選択肢ノードを作成
            if scene.choices:
                for j, choice in enumerate(scene.choices):
                    choice_x = x + (j - len(scene.choices)/2 + 0.5) * self.spacing_x
                    choice_y = y + self.spacing_y
                    
                    choice_cell = ET.SubElement(root, "mxCell",
                                              id=str(cell_id),
                                              value=choice.text,
                                              style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;",
                                              vertex="1",
                                              parent="1")
                    
                    choice_geometry = ET.SubElement(choice_cell, "mxGeometry",
                                                  x=str(choice_x), y=str(choice_y),
                                                  width=str(self.choice_width),
                                                  height=str(self.choice_height),
                                                  as_="geometry")
                    
                    # シーンから選択肢への矢印
                    edge_cell = ET.SubElement(root, "mxCell",
                                            id=str(cell_id + 1000),
                                            value="",
                                            style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;",
                                            edge="1",
                                            source=str(scene_to_id[scene.id]),
                                            target=str(cell_id),
                                            parent="1")
                    
                    edge_geometry = ET.SubElement(edge_cell, "mxGeometry",
                                                relative="1",
                                                as_="geometry")
                    
                    cell_id += 1
        
        # シーン間の接続を作成
        for scene in scenario.scenes:
            source_id = scene_to_id[scene.id]
            
            # 直接の次のシーンへの接続
            if scene.next_scene:
                target_scene = next((s for s in scenario.scenes if s.title == scene.next_scene), None)
                if target_scene:
                    target_id = scene_to_id[target_scene.id]
                    self._create_edge(root, cell_id, source_id, target_id)
                    cell_id += 1
            
            # 選択肢からの接続
            for choice in scene.choices:
                if choice.target_scene:
                    target_scene = next((s for s in scenario.scenes if s.title == choice.target_scene), None)
                    if target_scene:
                        target_id = scene_to_id[target_scene.id]
                        # 選択肢ノードのIDを計算（簡略化のため、直接接続）
                        self._create_edge(root, cell_id, source_id, target_id, choice.text)
                        cell_id += 1
        
        # XMLを文字列として返す
        return self._prettify_xml(mxgraph_model)
    
    def _calculate_positions(self, scenes: List[Scene]) -> Dict[str, Tuple[int, int]]:
        """シーンノードの位置を計算"""
        positions = {}
        
        for i, scene in enumerate(scenes):
            # 簡単な配置：縦に並べる
            x = self.start_x
            y = self.start_y + i * (self.node_height + self.spacing_y)
            positions[scene.id] = (x, y)
        
        return positions
    
    def _format_scene_text(self, scene: Scene) -> str:
        """シーンの表示テキストをフォーマット"""
        text = f"<b>{scene.title}</b><br/>"
        
        # 主要なセリフを追加（最初の2つまで）
        for i, dialogue in enumerate(scene.dialogues[:2]):
            text += f"{dialogue.character}: {dialogue.text[:30]}...<br/>"
        
        if len(scene.dialogues) > 2:
            text += f"... (+{len(scene.dialogues) - 2} more)"
        
        return text
    
    def _create_edge(self, root: ET.Element, edge_id: int, source_id: int, target_id: int, label: str = ""):
        """エッジ（矢印）を作成"""
        edge_cell = ET.SubElement(root, "mxCell",
                                id=str(edge_id),
                                value=label,
                                style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;",
                                edge="1",
                                source=str(source_id),
                                target=str(target_id),
                                parent="1")
        
        edge_geometry = ET.SubElement(edge_cell, "mxGeometry",
                                    relative="1",
                                    as_="geometry")
    
    def _prettify_xml(self, element: ET.Element) -> str:
        """XMLを整形して文字列として返す"""
        from xml.dom import minidom
        
        rough_string = ET.tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def save_flowchart(self, scenario: ScenarioStructure, filename: str):
        """フローチャートをファイルに保存"""
        xml_content = self.generate_flowchart(scenario)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"フローチャートを {filename} に保存しました。")

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
    
    # フローチャートを生成
    generator = FlowchartGenerator()
    generator.save_flowchart(scenario_structure, "sample_flowchart.drawio")


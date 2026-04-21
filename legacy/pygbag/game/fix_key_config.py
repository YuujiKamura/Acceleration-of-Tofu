#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import shutil
from game.constants import KEY_MAPPING_P1, KEY_MAPPING_P2, KEY_MAPPING, DEFAULT_KEY_MAPPING_P1, DEFAULT_KEY_MAPPING_P2, ACTION_NAMES

def fix_key_config():
    """L[RtBO̖C"""
    print("L[RtBOCc[")
    print("=" * 50)
    
    #obNAbv쐬
    if os.path.exists("key_config.json"):
        try:
            with open("key_config.json", "r") as f:
                config = json.load(f)
            
            shutil.copy("key_config.json", "key_config.json.backup")
            print("̐ݒt@CobNAbv܂")
            
            print("\n݂̐ݒ:")
            if "p1" in config:
                print(f"P1: {config['p1']}")
            else:
                print("P1̐ݒ肪܂")
            
            if "p2" in config:
                print(f"P2: {config['p2']}")
            else:
                print("P2̐ݒ肪܂")
                
            # KEY_MAPPING̏ԂmF
            print("\n݂KEY_MAPPING:")
            print(f"KEY_MAPPING_P1: {KEY_MAPPING_P1}")
            print(f"KEY_MAPPING_P2: {KEY_MAPPING_P2}")
            print(f"KEY_MAPPING: {KEY_MAPPING}")
            
            # ݒt@C𐮗
            new_config = {"p1": {}, "p2": {}}
            
            # P1̐ݒN[Abv
            if "p1" in config and config["p1"]:
                # ̃L[𐮐ɕϊ
                for k, v in config["p1"].items():
                    try:
                        key_int = int(k)
                        new_config["p1"][str(key_int)] = v
                    except ValueError:
                        print(f"x:sȃL[l '{k}' XLbv܂")
            else:
                # P1̐ݒ肪Ȃ΃ftHglݒ
                for k, v in DEFAULT_KEY_MAPPING_P1.items():
                    new_config["p1"][str(k)] = v
                print("P1ɃftHgݒgp܂")
            
            # P2̐ݒN[Abv
            if "p2" in config and config["p2"]:
                # ̃L[𐮐ɕϊ
                for k, v in config["p2"].items():
                    try:
                        key_int = int(k)
                        new_config["p2"][str(key_int)] = v
                    except ValueError:
                        print(f"x:sȃL[l '{k}' XLbv܂")
            else:
                # P2̐ݒ肪Ȃ΃ftHglݒ
                for k, v in DEFAULT_KEY_MAPPING_P2.items():
                    new_config["p2"][str(k)] = v
                print("P2ɃftHgݒgp܂")
            
            #K{ANVݒ肳Ă邩mF
            for player in ["p1", "p2"]:
                missing_actions = []
                for action in ACTION_NAMES:
                    if action not in new_config[player].values():
                        missing_actions.append(action)
                
                if missing_actions:
                    print(f"�x��: {player}��{', '.join(missing_actions)}�A�N�V��������`����Ă��܂���")
                    # �s�����Ă���A�N�V�������f�t�H���g�ݒ肩��⊮
                    default_map = DEFAULT_KEY_MAPPING_P1 if player == "p1" else DEFAULT_KEY_MAPPING_P2
                    for action in missing_actions:
                        for k, v in default_map.items():
                            if v == action and str(k) not in new_config[player]:
                                new_config[player][str(k)] = action
                                break
            
            # �V�����ݒ��ۑ�
            with open("key_config.json", "w") as f:
                json.dump(new_config, f, indent=2)
            print("\n�C����̐ݒ��ۑ����܂����B")
            
            # �L�[�}�b�s���O���X�V
            # P1�̐ݒ�
            KEY_MAPPING_P1.clear()
            for k, v in new_config["p1"].items():
                KEY_MAPPING_P1[int(k)] = v
            
            # P2�̐ݒ�
            KEY_MAPPING_P2.clear()
            for k, v in new_config["p2"].items():
                KEY_MAPPING_P2[int(k)] = v
            
            # �݊����̂��߂ɌÂ��}�b�s���O���X�V
            KEY_MAPPING.clear()
            KEY_MAPPING.update(KEY_MAPPING_P1)
            
            print("\n�C�����KEY_MAPPING:")
            print(f"KEY_MAPPING_P1: {KEY_MAPPING_P1}")
            print(f"KEY_MAPPING_P2: {KEY_MAPPING_P2}")
            print(f"KEY_MAPPING: {KEY_MAPPING}")
            
            print("\n�L�[�R���t�B�O�̏C�����������܂����B")
            
        except Exception as e:
            print(f"�ݒ�̏C���Ɏ��s���܂���: {e}")
            return False
    else:
        print("�ݒ�t�@�C����������܂���B�V�����ݒ�t�@�C�����쐬���܂��B")
        
        # �f�t�H���g�ݒ�ŐV�����ݒ�t�@�C�����쐬
        new_config = {
            "p1": {str(k): v for k, v in DEFAULT_KEY_MAPPING_P1.items()},
            "p2": {str(k): v for k, v in DEFAULT_KEY_MAPPING_P2.items()}
        }
        
        try:
            with open("key_config.json", "w") as f:
                json.dump(new_config, f, indent=2)
            print("�f�t�H���g�ݒ�t�@�C�����쐬���܂����B")
            return True
        except Exception as e:
            print(f"�ݒ�t�@�C���̍쐬�Ɏ��s���܂���: {e}")
            return False

if __name__ == "__main__":
    fix_key_config()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import shutil
from game.constants import *

def fix_key_config():
    """�L�[�R���t�B�O�̖����C��"""
    print("�L�[�R���t�B�O�C���c�[��")
    print("=" * 50)
    
    # �o�b�N�A�b�v���쐬
    if os.path.exists("key_config.json"):
        try:
            with open("key_config.json", "r") as f:
                config = json.load(f)
            
            shutil.copy("key_config.json", "key_config.json.backup")
            print("�����̐ݒ�t�@�C�����o�b�N�A�b�v���܂���")
            
            print("\n���݂̐ݒ�:")
            if "p1" in config:
                print(f"P1: {config['p1']}")
            else:
                print("P1�̐ݒ肪����܂���")
            
            if "p2" in config:
                print(f"P2: {config['p2']}")
            else:
                print("P2�̐ݒ肪����܂���")
                
            # KEY_MAPPING�̏�Ԃ��m�F
            print("\n���݂�KEY_MAPPING:")
            print(f"KEY_MAPPING_P1: {KEY_MAPPING_P1}")
            print(f"KEY_MAPPING_P2: {KEY_MAPPING_P2}")
            print(f"KEY_MAPPING: {KEY_MAPPING}")
            
            # �ݒ�t�@�C���𐮗�
            new_config = {"p1": {}, "p2": {}}
            
            # P1�̐ݒ���N���[���A�b�v
            if "p1" in config and config["p1"]:
                # ������̃L�[�𐮐��ɕϊ�
                for k, v in config["p1"].items():
                    try:
                        key_int = int(k)
                        new_config["p1"][str(key_int)] = v
                    except ValueError:
                        print(f"�x��: �s���ȃL�[�l '{k}' ���X�L�b�v���܂�")
            else:
                # P1�̐ݒ肪�Ȃ���΃f�t�H���g�l��ݒ�
                for k, v in DEFAULT_KEY_MAPPING_P1.items():
                    new_config["p1"][str(k)] = v
                print("P1�Ƀf�t�H���g�ݒ���g�p���܂�")
            
            # P2�̐ݒ���N���[���A�b�v
            if "p2" in config and config["p2"]:
                # ������̃L�[�𐮐��ɕϊ�
                for k, v in config["p2"].items():
                    try:
                        key_int = int(k)
                        new_config["p2"][str(key_int)] = v
                    except ValueError:
                        print(f"�x��: �s���ȃL�[�l '{k}' ���X�L�b�v���܂�")
            else:
                # P2�̐ݒ肪�Ȃ���΃f�t�H���g�l��ݒ�
                for k, v in DEFAULT_KEY_MAPPING_P2.items():
                    new_config["p2"][str(k)] = v
                print("P2�Ƀf�t�H���g�ݒ���g�p���܂�")
            
            # �K�{�A�N�V�������ݒ肳��Ă��邩�m�F
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

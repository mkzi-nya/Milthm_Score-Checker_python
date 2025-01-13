import json
import re
def load_beatmap_dict(dict_file):
    beatmap_dict = {}
    with open(dict_file, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.match(
                r'"([a-f0-9\-]+)":\s*{[^}]*category:\s*"([^"]+)"\s*name:\s*"([^"]+)"', line
            )
            if match:
                beatmap_id, category, name = match.groups()
                beatmap_dict[(name, category)] = beatmap_id
    return beatmap_dict

def convert_save_format(input_file, output_file, beatmap_dict):
    with open(input_file, 'r', encoding='utf-8') as file:
        raw_data = file.read()
    username = re.search(r"\[(.*?)\],\{", raw_data).group(1)
    records = re.findall(r"\[([^,\]]+),([^,\]]+),[\d.]+,(\d+),([\d.]+),(\d+)\]", raw_data)
    converted_data = {
        "UserName": username,
        "UserUUID": "a5206f20-986e-4164-9883-85fd2cee05e0",
        "LastSaveTime": "2024-09-28T21:18:32",
        "SaveVersionCode": 1,
        "SongRecords": []
    }
    for name, category, best_score, best_accuracy, best_level in records:
        key = (name, category)
        beatmap_id = beatmap_dict.get(key)
        if beatmap_id:
            best_level = int(best_level)
            if best_level == 0:
                achieved_status = [3, 4, 5]
            elif best_level == 1:
                achieved_status = [3, 4, 5]
            elif best_level == 2:
                achieved_status = [3, 4]
            else:
                achieved_status = [3]
            converted_data["SongRecords"].append({
                "BeatmapID": beatmap_id,
                "BestScore": int(best_score),
                "BestAccuracy": float(best_accuracy),
                "BestLevel": best_level,
                "AchievedStatus": achieved_status
            })
        else:
            print(f"未找到对应的BeatmapID: {key}")
    json_data = json.dumps(converted_data, ensure_ascii=False, separators=(',', ':'))
    additional_content = (',"MarkRecords":[{"MarkName":"tip_welcome_read","Mark":true},{"MarkName":"episode_story.main.0.1_read","Mark":true},{"MarkName":"tip_judgement_read","Mark":true},{"MarkName":"tip_bluetooth_read","Mark":true},{"MarkName":"tip_rain_read","Mark":true},{"MarkName":"tip_checkstate_read","Mark":true},{"MarkName":"tip_about-us_read","Mark":true},{"MarkName":"tip_susan_read","Mark":true},{"MarkName":"tip_hold-tricks_read","Mark":true},{"MarkName":"tip_level-rule_read","Mark":true},{"MarkName":"tip_reality_read","Mark":true},{"MarkName":"tip_star_read","Mark":true},{"MarkName":"tip_who-are-you_read","Mark":true},{"MarkName":"tip_what-is-downpour_read","Mark":true},{"MarkName":"tip_what-is-heart_read","Mark":true},{"MarkName":"tip_coffee_read","Mark":true},{"MarkName":"tip_sleep_read","Mark":true},{"MarkName":"tip_do-you-know_read","Mark":true},{"MarkName":"tip_or-scene-illustration_read","Mark":true},{"MarkName":"episode_story.main.0.2_read","Mark":true},{"MarkName":"episode_story.main.0.3_read","Mark":true},{"MarkName":"episode_story.main.0.4_read","Mark":true},{"MarkName":"episode_story.main.0.5_read","Mark":true},{"MarkName":"episode_story.main.0.6_read","Mark":true},{"MarkName":"RainCity-Cloudburst","Mark":true},{"MarkName":"DestinyDay-Cloudburst","Mark":true},{"MarkName":"episode_main_story_1_1_read","Mark":true},{"MarkName":"episode_main_story_1_2_read","Mark":true},{"MarkName":"episode_main_story_1_3_read","Mark":true},{"MarkName":"episode_main_story_1_4_read","Mark":true},{"MarkName":"episode_main_story_1_5_read","Mark":true},{"MarkName":"hyper_memories","Mark":true},{"MarkName":"episode_main_story_1_6_read","Mark":true},{"MarkName":"regnaissance-Cloudburst","Mark":true},{"MarkName":"contrasty_angels-Cloudburst","Mark":true},{"MarkName":"episode_main_story_1_7_read","Mark":true},{"MarkName":"RainWorld","Mark":true},{"MarkName":"episode_story.rainworld.0.2_read","Mark":true},{"MarkName":"episode_story.rainworld.0.1_read","Mark":true},{"MarkName":"episode_story.notanote.1_read","Mark":true},{"MarkName":"episode_story.notanote.2_read","Mark":true},{"MarkName":"episode_story.notanote.3_read","Mark":true},{"MarkName":"episode_story.notanote.4_read","Mark":true},{"MarkName":"episode_story.rainworld.0.3_read","Mark":true},{"MarkName":"episode_story.rainworld.1.1_read","Mark":true},{"MarkName":"episode_story.rainworld.1.2_read","Mark":true},{"MarkName":"episode_story.rainworld.1.3_read","Mark":true},{"MarkName":"episode_story.rainworld.2.1_read","Mark":true},{"MarkName":"episode_story.rainworld.2.2_read","Mark":true},{"MarkName":"episode_story.rainworld.2.3_read","Mark":true},{"MarkName":"episode_story.notanote.5_read","Mark":true},{"MarkName":"DogbiteSP","Mark":true}],"ImmerseProgresses":[{"Tag":"0","Value":1.0},{"Tag":"chapter1","Value":1.0},{"Tag":"RainWorld","Value":1.0},{"Tag":"notanote","Value":1.0}],"Agreements":[{"ID":"eula","AcceptTime":"2024/9/130:47:46","AgreementUpdateTime":"2023/10/210:00:00","AgreementVersion":2023102104},{"ID":"privacy_policy-zh","AcceptTime":"2024/9/130:47:49","AgreementUpdateTime":"2023/10/270:00:00","AgreementVersion":2023102704}],"Offsets":[{"DeviceID":"AndroidOboe//h2wwiredheadphones","Offset":-40.0},{"DeviceID":"AndroidOboe//VOG-AL00built-inspeaker","Offset":0.0},{"DeviceID":"AndroidOboe//SK19BluetoothdevicesupportingtheA2DPprofile","Offset":330.0},{"DeviceID":"AndroidOboe//h2wwiredheadset","Offset":0.0},{"DeviceID":"CoreAudio/SK19","Offset":300.0},{"DeviceID":"CoreAudio/MacBookProのスピーカー","Offset":0.0}],"LatestAudioDeviceID":"AndroidOboe//h2wwiredheadphones","SongListSorting":3,"ReverseSongListSorting":false,"LastSelectChapterID":"All","LastReadChapterID":"notanote","ChapterSelectPreferences":[{"ChapterID":"All","LastSelectSongID":"5f94aacc-fba5-46a9-8bd4-cbe341ef511d","LastSelectDifficulty":"Cloudburst"},{"ChapterID":"Chapter0","LastSelectSongID":"5f94aacc-fba5-46a9-8bd4-cbe341ef511d","LastSelectDifficulty":"Cloudburst"},{"ChapterID":"Chapter1","LastSelectSongID":"8e5c851e-458d-4524-a1b7-3dd5eee95d29","LastSelectDifficulty":"Cloudburst"},{"ChapterID":"Introduction","LastSelectSongID":"0e7a0933-fc30-44b7-87ec-cef6384dd5a0","LastSelectDifficulty":"Cloudburst"},{"ChapterID":"Notanote","LastSelectSongID":"c41460e1-0352-4b89-bcd7-b49c90a20e82","LastSelectDifficulty":"Cloudburst"},{"ChapterID":"RainWorld","LastSelectSongID":"70c13150-a2af-49cc-b228-8878c7bb1815","LastSelectDifficulty":"Cloudburst"},{"ChapterID":"Single","LastSelectSongID":"d2a71352-f0a0-4198-a9bb-dde7db2f4b61","LastSelectDifficulty":"Cloudburst"}]}')
    final_output = json_data[:-1] + additional_content
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(final_output)
if __name__ == "__main__":
    dict_file = "BeatmapID字典.txt"
    input_file = "save.txt"
    output_file = "save.json"

    beatmap_dict = load_beatmap_dict(dict_file)
    convert_save_format(input_file, output_file, beatmap_dict)

    print("存档转换完成！")

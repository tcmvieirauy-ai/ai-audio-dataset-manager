from pathlib import Path

BASE_DIR = Path(__file__).parent

INCOMING = BASE_DIR / "incoming"

CATEGORIES = {
    "WorkOffice": [
        "MeetingRecording",
        "CustomerCommunicationRecording",
        "InterviewRecording",
        "WorkInstructionRecording",
        "OnlineMeetingRecording"
    ],

    "StudyEducation": [
        "ClassroomRecording",
        "LectureTrainingRecording",
        "SelfStudyRecording",
        "LanguageLearningRecording"
    ],

    "DailyLife": [
        "MemoRecording",
        "FamilyRecords",
        "InspirationRecord",
        "EnvironmentalSoundCollection"
    ],

    "CommunicationRetention": [
        "ImportantCallRecording",
        "DisputeEvidenceRecording",
        "FoodDeliveryRecording"
    ],

    "BusinessService": [
        "ClientInteractionRecording",
        "OrderDiscussionRecording",
        "CustomerSupportCallRecording",
        "ServiceRequestRecording",
        "BusinessMeetingRecording"
    ],

    "ContentCreation": [
        "VoiceCreation",
        "VideoDubbing",
        "MusicComposition"
    ],

    "LegalSecurity": [
        "EvidenceRecording",
        "EmergencyHelpRecording"
    ],

    "SocialEntertainment": [
        "FriendGatheringRecording",
        "GameVoiceRecording"
    ],

    "OtherSpecialScenarios": [
        "EquipmentTestingRecording",
        "MedicalConsultationRecording"
    ]
}


def main():
    print("\nCriando estrutura de pastas do incoming...\n")

    total = 0

    for primary, secondary_list in CATEGORIES.items():
        for secondary in secondary_list:
            folder = INCOMING / primary / secondary
            folder.mkdir(parents=True, exist_ok=True)
            print(f"Criada: incoming/{primary}/{secondary}")
            total += 1

    print(f"\nTotal de pastas criadas/verificadas: {total}")


if __name__ == "__main__":
    main()
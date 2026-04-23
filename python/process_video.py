import sys
from app import process_video, get_predictor_model

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    model = get_predictor_model()
    process_video(input_path, model, output_path)

    print("DONE")

from pathlib import Path
from uuid import uuid4

from modules.data_engine import load_dataset
from modules.database import (
    save_dataset_record,
    get_user_datasets,
    get_user_dataset,
    delete_user_dataset_record
)


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

MAX_FILE_SIZE = 50 * 1024 * 1024

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def save_uploaded_dataset(user_id, uploaded_file):

    original_filename = Path(uploaded_file.name).name
    extension = Path(original_filename).suffix.lower()
    file_bytes = uploaded_file.getvalue()

    if extension not in ALLOWED_EXTENSIONS:
        return False, "Only CSV and Excel files are supported.", None

    if not file_bytes:
        return False, "The uploaded file is empty.", None

    if len(file_bytes) > MAX_FILE_SIZE:
        return False, "File size must not exceed 50 MB.", None

    try:
        # Validate and load the dataset before saving
        dataframe = load_dataset(file_bytes, original_filename)

        # Create a separate folder for each user
        user_folder = UPLOAD_DIR / f"user_{user_id}"
        user_folder.mkdir(parents=True, exist_ok=True)

        # Generate a unique filename
        stored_filename = f"{uuid4().hex}{extension}"
        file_path = user_folder / stored_filename

        # Save original file bytes
        file_path.write_bytes(file_bytes)

        try:
            dataset_id = save_dataset_record(
                user_id,
                original_filename,
                stored_filename,
                str(file_path),
                len(dataframe),
                len(dataframe.columns)
            )

        except Exception:
            file_path.unlink(missing_ok=True)
            raise

        return True, "Dataset uploaded successfully.", dataset_id

    except Exception as error:
        return False, f"Upload failed: {error}", None


def get_my_datasets(user_id):
    return get_user_datasets(user_id)


def load_my_dataset(dataset_id, user_id):

    dataset = get_user_dataset(dataset_id, user_id)

    if dataset is None:
        raise ValueError("Dataset not found or access denied.")

    file_path = Path(dataset["file_path"])

    if not file_path.is_file():
        raise FileNotFoundError("Dataset file is missing.")

    file_bytes = file_path.read_bytes()

    return load_dataset(
        file_bytes,
        dataset["original_filename"]
    )


def delete_my_dataset(dataset_id, user_id):

    dataset = get_user_dataset(dataset_id, user_id)

    if dataset is None:
        return False

    deleted = delete_user_dataset_record(dataset_id, user_id)

    if deleted:
        file_path = Path(dataset["file_path"])
        file_path.unlink(missing_ok=True)

    return deleted

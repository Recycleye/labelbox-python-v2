from pathlib import Path

from loguru import logger
from typing import Optional, Tuple
from PIL import Image

import imagesize
import io

from .path import PathSerializerMixin
from labelbox.data.annotation_types import Label
from labelbox.data.cloud.blobstorage import (
    create_blobstorage_client,
    extract_file_path,
    get_connection_string,
)

from azure_utils.blob import get_blob_metadata, set_blob_metadata

class CocoImage(PathSerializerMixin):
    id: int
    width: int
    height: int
    file_name: Path
    license: Optional[int] = None
    flickr_url: Optional[str] = None
    coco_url: Optional[str] = None


def get_image_id(label: Label, idx: int) -> int:
    if label.data.file_path is not None:
        file_name = label.data.file_path.replace(".jpg", "")
        if file_name.isdecimal():
            return file_name
    return idx


def get_image(
    label: Label,
    image_path: str,
    image_id: str,
    cloud_provider=None,
    azure_storage_container=None,
) -> CocoImage:
    """Extract dimensions from an image at 'image_path'.
    The path may be local or a path in a cloud storage service.
    If on cloud storage, 'image_path' should be used together with 'cloud_provider'.
    Currently, possible values for 'cloud_provider' are:
        - azure
    """

    if not cloud_provider:
        path = Path(image_path, f"{image_id}.jpg")
        if not path.exists():
            im = Image.fromarray(label.data.value)
            im.save(path)
            w, h = im.size
        else:
            w, h = imagesize.get(str(path))
        return CocoImage(
            id=image_id, width=w, height=h, file_name=Path(path).name
        )

    elif cloud_provider == "azure":
        conn = get_connection_string()
        client = create_blobstorage_client(conn, azure_storage_container)
        file_path = extract_file_path(label.data.url)

        logger.info(f"Checking size of image in: {file_path}, from blobstorage")
        # Check is done on the image if height and width exists as metadata
        image_metadata = get_blob_metadata(
            azure_connection=conn,
            azure_container_name=azure_storage_container,
            azure_blob_name=file_path
        )
        if 'height' in image_metadata and 'width' in image_metadata:
            # Metadata exists and h and w taken from this instead
            h = image_metadata['height']
            w = image_metadata['width']
        else:
            # Metadata doesn't exist so download is required
            logger.warning(f"Downloading {file_path} from blobstorage, height and width metadata"
                           f"for the image does not exist")
            image = client.download_blob(file_path).readall()
            img = Image.open(io.BytesIO(image))
            h, w = img.height, img.width

            # Setting the metadata since it doesn't exist
            image_metadata = {'height': str(h), 'width': str(w)}
            logger.info(f"As metadata for the image doesn't exist, "
                        f"writing metadata for file: {file_path}, {image_metadata}")
            set_blob_metadata(
                azure_connection=conn,
                azure_container_name=azure_storage_container,
                azure_blob_name=file_path,
                metadata=image_metadata
            )

        return CocoImage(
            id=image_id, width=w, height=h, file_name=Path(label.data.url.split('?')[0]).name
        )


def id_to_rgb(id: int) -> Tuple[int, int, int]:
    digits = []
    for _ in range(3):
        digits.append(id % 256)
        id //= 256
    return digits


def rgb_to_id(red: int, green: int, blue: int) -> int:
    id = blue * 256 * 256
    id += (green * 256)
    id += red
    return id

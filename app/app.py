from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Query
from sqlalchemy.orm import Session
import schemas
from db import SessionLocal, Meme
from minio import Minio
from minio.error import S3Error
from typing import List

app = FastAPI(
    title="Meme API",
    description="API for creating, retrieving, updating, and deleting memes",
    version="1.0.0",
    docs_url="/documentation",
    redoc_url=None
)

# Настройка клиента MinIO
minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Название корзины MinIO
MINIO_BUCKET = "memes"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/memes/", response_model=List[schemas.Meme], summary="Retrieve a list of memes")
def read_memes(skip: int = Query(default=0, description="Number of items to skip for pagination"),
               limit: int = Query(default=100, description="Maximum number of items to return per page"),
               db: Session = Depends(get_db)):
    """
    Retrieves a paginated list of memes from the database.

    - **skip**: Number of items to skip (for pagination).
    - **limit**: Maximum number of items to return (for pagination).
    """
    memes = db.query(Meme).offset(skip).limit(limit).all()
    return memes


@app.get("/memes/{meme_id}", response_model=schemas.Meme, summary="Retrieve a specific meme by ID")
def read_meme(meme_id: int, db: Session = Depends(get_db)):
    """
        Retrieves a specific meme by its ID.

        - **meme_id**: The ID of the meme to retrieve.
        """
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if meme is None:
        raise HTTPException(status_code=404, detail="Meme not found")
    return meme


@app.post("/memes/", response_model=schemas.Meme, status_code=201, summary="Create a new meme with image and text")
async def create_meme(meme: schemas.MemeCreate = Depends(), file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
        Creates a new meme with the given image and text.

        - **meme**: Meme creation object including title and description.
        - **file**: Image file to upload.
        """
    file_location = f"memes/{file.filename}"
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
        minio_client.put_object(
            MINIO_BUCKET, file.filename, file.file, file.content_length
        )
        image_url = f"http://{minio_client.endpoint}/{MINIO_BUCKET}/{file.filename}"
        new_meme = Meme(title=meme.title, description=meme.description, image_url=image_url)
        db.add(new_meme)
        db.commit()
        db.refresh(new_meme)
        return new_meme
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


@app.put("/memes/{meme_id}", response_model=schemas.Meme, summary="Update an existing meme")
async def update_meme(meme_id: int, meme: schemas.MemeUpdate, file: UploadFile = File(None),
                      db: Session = Depends(get_db)):
    """
    Updates an existing meme. Can update title, description, and/or image.

    - **meme_id**: The ID of the meme to update.
    - **meme**: Meme update object including new title and description.
    - **file**: New image file to upload, if any.
    """
    db_meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Meme not found")
    if file:
        try:
            minio_client.remove_object(MINIO_BUCKET, db_meme.image_url.split('/')[-1])
            minio_client.put_object(
                MINIO_BUCKET, file.filename, file.file, file.content_length
            )
            db_meme.image_url = f"http://{minio_client.endpoint}/{MINIO_BUCKET}/{file.filename}"
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to update image: {str(e)}")
    db_meme.title = meme.title
    db_meme.description = meme.description
    db.commit()
    return db_meme


@app.delete("/memes/{meme_id}",  status_code=204, summary="Delete a meme")
def delete_meme(meme_id: int, db: Session = Depends(get_db)):
    """
    Deletes a meme by its ID.

    - **meme_id**: The ID of the meme to delete.
    """
    db_meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Meme not found")
    try:
        minio_client.remove_object(MINIO_BUCKET, db_meme.image_url.split('/')[-1])
        db.delete(db_meme)
        db.commit()
        return {"ok": True}
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

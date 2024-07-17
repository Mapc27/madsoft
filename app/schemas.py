from pydantic import BaseModel, Field, HttpUrl


class MemeBase(BaseModel):
    title: str = Field(None, description="Title of the meme")
    description: str = Field(None, description="Description of the meme",)

    class Config:
        orm_mode = True


class MemeCreate(MemeBase):
    pass


class MemeUpdate(MemeBase):
    pass


class Meme(MemeBase):
    id: int
    image_url: HttpUrl


curl -X POST "http://localhost:8000/memes/"  -H "Content-Type: multipart/form-data"    -F 'meme={"title": "Смешной мем", "description": "Описание смешного мема"};type=application/json'  -F "file=@C:\Users\Mapct\projects\madsoft\img.jpg


curl -X POST "http://localhost:8000/memes/" -H "Content-Type: multipart/form-data" -F 'meme={"title": "Смешной мем", "description": "Описание смешного мема"};type=application/json' -F "file=@C:\Users\Mapct\projects\madsoft\img.jpg"

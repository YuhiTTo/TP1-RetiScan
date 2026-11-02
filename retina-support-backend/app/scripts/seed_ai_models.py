from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.ai_model import AIModel


AI_MODELS = [
    {
        "nombre": "EfficientNetB3+SE",
        "version": "finetune_best",
        "objetivo": "RETINOPATIA_DIABETICA",
        "ruta_modelo": (
            "models/RD/efficientnetb3_se/"
            "efficientnetb3_se_finetune_best.keras"
        ),
    },
    {
        "nombre": "ResNet50V2",
        "version": "finetune_best",
        "objetivo": "GLAUCOMA",
        "ruta_modelo": (
            "models/glaucoma/resnet50v2/"
            "resnet50v2_finetune_best.keras"
        ),
    },
]


def seed_ai_models():
    db = SessionLocal()

    try:
        for model_data in AI_MODELS:

            existing_model = db.execute(
                select(AIModel).where(
                    AIModel.nombre == model_data["nombre"],
                    AIModel.version == model_data["version"]
                )
            ).scalar_one_or_none()

            if existing_model:
                print(
                    f"Ya existe: "
                    f"{existing_model.nombre} "
                    f"({existing_model.objetivo})"
                )
                continue

            model = AIModel(
                nombre=model_data["nombre"],
                version=model_data["version"],
                objetivo=model_data["objetivo"],
                ruta_modelo=model_data["ruta_modelo"],
                estado="ACTIVO"
            )

            db.add(model)

        db.commit()

        print()
        print("Modelos IA verificados correctamente.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_ai_models()

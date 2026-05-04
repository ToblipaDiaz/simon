from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Evidence(BaseModel):
    quote: str = Field(..., description="Cita textual breve del transcript (tal cual se dijo)")
    start_sec: Optional[float] = Field(..., description="Inicio en segundos (puede ser null si no se puede ubicar)")
    end_sec: Optional[float] = Field(..., description="Fin en segundos (puede ser null si no se puede ubicar)")

class FieldValue(BaseModel):
    value: Optional[str] = Field(..., description="Valor solo si se dijo explícitamente. Si no, null.")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidencia(s) del transcript para este campo")

class PerinatalDetails(BaseModel):
    pregnancy_controlled: FieldValue = Field(...)
    pregnancy_control_from_week: FieldValue = Field(...)
    pregnancy_diseases: FieldValue = Field(...)
    fetal_movements: FieldValue = Field(...)

    delivery_type: FieldValue = Field(...)
    delivery_complications: FieldValue = Field(...)
    fetal_distress: FieldValue = Field(...)

    gestational_age_weeks: FieldValue = Field(...)
    birth_weight: FieldValue = Field(...)
    birth_length: FieldValue = Field(...)
    birth_head_circumference: FieldValue = Field(...)

    neonatal_disease: FieldValue = Field(...)
    discharged_with_mother: FieldValue = Field(...)
    neonatal_hospitalization_reason: FieldValue = Field(...)

class DevelopmentDetails(BaseModel):
    delay_gross_motor: FieldValue = Field(...)
    delay_fine_motor: FieldValue = Field(...)
    delay_social: FieldValue = Field(...)
    delay_language: FieldValue = Field(...)
    milestones: FieldValue = Field(...)

class FamilyDetails(BaseModel):
    mother_history: FieldValue = Field(...)
    father_history: FieldValue = Field(...)
    consanguinity: FieldValue = Field(...)
    siblings: FieldValue = Field(...)

class IndicationsDetails(BaseModel):
    general: FieldValue = Field(...)
    school: FieldValue = Field(...)
    meds: FieldValue = Field(...)
    followup: FieldValue = Field(...)
    referrals: FieldValue = Field(...)

class ClinicalNoteJSON(BaseModel):
    specialty: Literal["neurologia_pediatrica"] = "neurologia_pediatrica"

    visit_type: FieldValue = Field(..., description="INGRESO o CONTROL si se dijo")
    patient_name: FieldValue = Field(..., description="Nombre si se dijo")
    patient_age: FieldValue = Field(..., description="Edad actual texto libre si se dijo (ej: 7 años 3 meses)")
    patient_sex: FieldValue = Field(..., description="Sexo si se dijo")
    brought_by: FieldValue = Field(..., description="MADRE/PADRE/AMBOS/OTRO si se dijo")
    informant: FieldValue = Field(..., description="Informante si se dijo")

    chief_complaint: FieldValue = Field(..., description="Motivo de consulta literal")

    hpi_onset: FieldValue = Field(...)
    hpi_course: FieldValue = Field(...)
    hpi_frequency: FieldValue = Field(...)
    hpi_duration: FieldValue = Field(...)
    hpi_triggers: FieldValue = Field(...)
    hpi_relief: FieldValue = Field(...)

    neuro_symptoms: List[str] = Field(default_factory=list, description="Síntomas mencionados, sin inferir")

    past_medical_history: FieldValue = Field(...)
    allergies: FieldValue = Field(...)
    meds: FieldValue = Field(...)

    family: FamilyDetails = Field(...)
    perinatal: PerinatalDetails = Field(...)
    development: DevelopmentDetails = Field(...)

    exam_neuro: FieldValue = Field(...)
    exams_reviewed: FieldValue = Field(...)
    diagnostic_hypothesis: FieldValue = Field(...)
    suspicion_or_confirmed: FieldValue = Field(..., description="Sospecha/Confirmado si se dijo explícitamente")

    indications: IndicationsDetails = Field(...)

    red_flags_mentioned: List[str] = Field(default_factory=list, description="Banderas rojas solo si se dijeron")

    missing_questions: List[str] = Field(default_factory=list, description="Preguntas faltantes en orden clínico")
    contradictions: List[str] = Field(default_factory=list, description="Contradicciones detectadas")
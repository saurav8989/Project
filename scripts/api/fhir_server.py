import sys
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Setup paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
fhir_data_dir = project_root / "data" / "fhir"

# Initialize FastAPI
app = FastAPI(
    title="DHIS2 FHIR Reference API",
    description="A REST API serving HL7 FHIR Measure and MeasureReport resources generated from Nepal DHIS2 Immunization Data.",
    version="1.0.0"
)

@app.get("/", tags=["Immunization"], summary="Immunization")
def health_check():
    """Simple health check endpoint."""
    return {"status": "online", "message": "DHIS2 FHIR Reference API is running."}

@app.get("/fhir/Measure", tags=["FHIR Resources"])
def get_all_measures():
    """Returns the Master Bundle containing all 18 Vaccine Measure blueprints."""
    master_measure_file = fhir_data_dir / "master_measures_bundle.json"
    if not master_measure_file.exists():
        raise HTTPException(status_code=404, detail="Master Measure Bundle not found.")
    
    with open(master_measure_file, "r") as f:
        data = json.load(f)
    return JSONResponse(content=data)

@app.get("/fhir/MeasureReport", tags=["FHIR Resources"])
def get_all_measurereports():
    """Returns the Master Bundle containing all 1,080 clinical MeasureReports."""
    master_mr_file = fhir_data_dir / "master_measurereports_bundle.json"
    if not master_mr_file.exists():
        raise HTTPException(status_code=404, detail="Master MeasureReport Bundle not found.")
    
    with open(master_mr_file, "r") as f:
        data = json.load(f)
    return JSONResponse(content=data)

@app.get("/fhir/Measure/{measure_id}", tags=["FHIR Resources"])
def get_measure_by_id(measure_id: str):
    """
    Search for a specific Measure Blueprint by its exact ID.
    Example ID to test: measure-bcg
    """
    measure_file = fhir_data_dir / "measures" / f"{measure_id}.json"
    
    if not measure_file.exists():
        raise HTTPException(status_code=404, detail=f"Measure with ID '{measure_id}' not found.")
    
    with open(measure_file, "r") as f:
        data = json.load(f)
    return JSONResponse(content=data)

@app.get("/fhir/MeasureReport/{report_id}", tags=["FHIR Resources"])
def get_measurereport_by_id(report_id: str):
    """
    Search for a specific MeasureReport by its exact ID.
    Example ID to test: measure-bcg-row-1
    """
    # Search the month-wise directory for the specific JSON file
    search_dir = fhir_data_dir / "monthwise_measure_report"
    found_files = list(search_dir.rglob(f"{report_id}.json"))
    
    if not found_files:
        raise HTTPException(status_code=404, detail=f"MeasureReport with ID '{report_id}' not found.")
    
    with open(found_files[0], "r") as f:
        data = json.load(f)
    return JSONResponse(content=data)

if __name__ == "__main__":
    import uvicorn
    print("Starting FHIR Reference API on http://127.0.0.1:8000")
    print("Documentation available at http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)

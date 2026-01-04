from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import joblib
import os
import shap
import numpy as np

# Lokasi model
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "random_forest_preeclampsia_model.pkl"
)

_rf_model = None
_shap_explainer = None


def get_rf_model():
    """Load RandomForest model sekali saja."""
    global _rf_model
    if _rf_model is None:
        _rf_model = joblib.load(MODEL_PATH)
    return _rf_model


def get_shap_explainer():
    """Load SHAP explainer sekali saja."""
    global _shap_explainer
    if _shap_explainer is None:
        model = get_rf_model()
        _shap_explainer = shap.TreeExplainer(model)
    return _shap_explainer


def prediksi_model(
    usia, gravida, para, abortus, usia_kehamilan,
    tinggi_badan, berat_badan, sistolik, diastolik, hemoglobin
):
    """Prediksi model + hitungan BMI & MAP."""

    model = get_rf_model()

    # Hitung BMI dan MAP
    tinggi_meter = tinggi_badan / 100.0
    bmi = berat_badan / (tinggi_meter ** 2) if tinggi_meter > 0 else 0
    map_mmHg = (2 * diastolik + sistolik) / 3.0

    fitur = [[
        usia,
        gravida,
        para,
        abortus,
        usia_kehamilan,
        berat_badan,
        tinggi_badan,
        sistolik,
        diastolik,
        map_mmHg,
        hemoglobin,
        bmi,
    ]]

    # Hasil prediksi angka (0/1)
    pred_value = model.predict(fitur)[0]

    if pred_value == 1:
        risiko = "PREEKLAMSIA"
        warna = "danger"
        deskripsi = "Model mendeteksi kemungkinan preeklamsia."
    else:
        risiko = "NORMAL"
        warna = "success"
        deskripsi = "Tidak terdeteksi tanda preeklamsia."

    return risiko, warna, deskripsi, fitur, pred_value


@login_required
def input_data(request):
    return render(request, "prediksi/input_data.html")


@login_required
def predict_risk(request):
    if request.method == "POST":

        # ------------------ Ambil input user ------------------ #
        try:
            usia = int(request.POST.get("usia", 0))
            gravida = int(request.POST.get("gravida", 0))
            para = int(request.POST.get("para", 0))
            abortus = int(request.POST.get("abortus", 0))
            usia_kehamilan = int(request.POST.get("usia_kehamilan", 0))
            tinggi_badan = float(request.POST.get("tinggi_badan", 0))
            berat_badan = float(request.POST.get("berat_badan", 0))
            sistolik = int(request.POST.get("sistolik", 0))
            diastolik = int(request.POST.get("diastolik", 0))
            hemoglobin = float(request.POST.get("hemoglobin", 0))
            kejang = int(request.POST.get("kejang", 0))
        except:
            return render(request, "prediksi/input_data.html", {
                "error": "Input tidak valid."
            })

        # ------------------ Prediksi model ------------------ #
        try:
            risiko, warna, deskripsi, fitur, pred_value = prediksi_model(
                usia, gravida, para, abortus, usia_kehamilan,
                tinggi_badan, berat_badan, sistolik, diastolik, hemoglobin
            )

            # --- LOGIC EKLAMSIA ---
            # Jika terdeteksi Preeklamsia DAN ada Kejang -> Eklamsia
            if risiko == "PREEKLAMSIA" and kejang == 1:
                risiko = "EKLAMSIA"
                deskripsi = "Model mendeteksi kemungkinan Eklamsia."
                # Warna bisa tetap danger atau dibedakan jika mau (misal merah lebih tua)
                # warna = "danger" 

        except Exception as e:
            return render(request, "prediksi/input_data.html", {
                "error": f"Error model: {e}"
            })

        # ------------------ SHAP ------------------ #
        explainer = get_shap_explainer()
        shap_values = explainer.shap_values(np.array(fitur))

        # Handle model SHAP output (bisa list atau array)
        if isinstance(shap_values, list):
            if len(shap_values) == 1:
                shap_for_patient = shap_values[0][0]
            else:
                shap_for_patient = shap_values[pred_value][0]
        else:
            shap_for_patient = shap_values[0]

        feature_names = [
            "Usia",
            "Gravida",
            "Para",
            "Abortus",
            "Usia Kehamilan",
            "Berat Badan",
            "Tinggi Badan",
            "Sistolik",
            "Diastolik",
            "MAP",
            "Hemoglobin",
            "BMI"
        ]

        # ------------------ Fix SHAP scalar error ------------------ #
        importance = []
        for name, val in zip(feature_names, shap_for_patient):

            try:
                nilai_scalar = float(np.abs(val).item())
            except:
                nilai_scalar = float(np.abs(val).flatten()[0])

            importance.append({
                "fitur": name,
                "nilai": round(nilai_scalar, 4)
            })

        # Urutkan dari paling berpengaruh
        importance_sorted = sorted(
            importance,
            key=lambda x: x["nilai"],
            reverse=True
        )

        # Hitung ulang BMI & MAP untuk display
        tinggi_meter = tinggi_badan / 100.0
        bmi = berat_badan / (tinggi_meter ** 2) if tinggi_meter > 0 else 0
        map_mmHg = (2 * diastolik + sistolik) / 3.0

        # ------------------ Data ke template ------------------ #
        context = {
            "risiko": risiko,
            "deskripsi": deskripsi,
            "warna": warna,

            "usia": usia,
            "gravida": gravida,
            "para": para,
            "abortus": abortus,
            "usia_kehamilan": usia_kehamilan,
            "tinggi_badan": tinggi_badan,
            "berat_badan": berat_badan,
            "sistolik": sistolik,
            "diastolik": diastolik,
            "hemoglobin": hemoglobin,
            "bmi": round(bmi, 1),
            "map_mmHg": round(map_mmHg, 1),

            "importance": importance_sorted,
        }

        return render(request, "prediksi/hasil.html", context)

    return render(request, "prediksi/input_data.html")

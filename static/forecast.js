document.addEventListener('DOMContentLoaded', () => {
    console.log(window.location.search);


    const datasetNameFromURL = new URLSearchParams(window.location.search).get('dataset_name');
    console.log("Extracted Dataset:", datasetNameFromURL);
    const datasetSpan = document.getElementById('dataset-name');  // <span> for display
    const datasetInput = document.getElementById('dataset_name'); // hidden input

    const forecastForm = document.getElementById("forecast-form");
    const forecastResult = document.getElementById("forecast-result");

    // ✅ Set values from URL at page load
    if (datasetNameFromURL) {
        if (datasetSpan) {
            datasetSpan.textContent = datasetNameFromURL;
            console.log(`Displayed dataset: ${datasetNameFromURL}`);
        }
        if (datasetInput) {
            datasetInput.value = datasetNameFromURL;
            console.log(`Hidden input set: ${datasetInput.value}`);
        }
    } else {
        // If no dataset name in URL, show error
        if (datasetSpan) {
            datasetSpan.textContent = "❌ No dataset selected";
        }
    }

    // 🚀 Submit event
    forecastForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        // 💡 Just in case, set hidden input value again before reading form
        if (datasetNameFromURL && datasetInput) {
            datasetInput.value = datasetNameFromURL;
        }

        const formData = new FormData(forecastForm);

        // Debug logs
        console.log("Form Values Before Validation:");
        for (const [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }

        // 🚨 Validation
        if (!formData.get("dataset_name") || !formData.get("dependent_col") || !formData.get("steps")) {
            forecastResult.innerHTML = `<p class="error">❌ Please fill all required fields.</p>`;
            return;
        }

        try {
            const response = await fetch("/forecast", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            console.log("Response Data:", data);

            if (data.error) {
                forecastResult.innerHTML = `<p class="error">❌ ${data.error}</p>`;
            } else {
                displayForecastTable(data);
            }
        } catch (error) {
            forecastResult.innerHTML = `<p class="error">❌ An error occurred: ${error}</p>`;
        }
    });

    // Display forecast results
    function displayForecastTable(forecastData) {
    forecastResult.innerHTML = "";

    for (const model in forecastData) {
        const modelData = forecastData[model];

        if (!modelData || !Array.isArray(modelData)) {
            forecastResult.innerHTML += `
                <div class="forecast-model result-card">
                    <h3>🔹 ${model}</h3>
                    <p class="error">❌ Invalid forecast data.</p>
                </div>`;
            continue;
        }

        let tableHTML = `
            <div class="forecast-model result-card">
                <h3>🔹 ${model}</h3>
                <table class="forecast-table">
                    <thead>
                        <tr>
                            <th>Step</th>
                            <th>Forecast</th>
                            <th>Lower Conf.</th>
                            <th>Upper Conf.</th>
                        </tr>
                    </thead>
                    <tbody>`;

        modelData.forEach((entry, index) => {
            tableHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${entry.forecast.toFixed(2)}</td>
                    <td>${entry.lower_conf_int ? entry.lower_conf_int.toFixed(2) : "N/A"}</td>
                    <td>${entry.upper_conf_int ? entry.upper_conf_int.toFixed(2) : "N/A"}</td>
                </tr>`;
        });

        tableHTML += `
                    </tbody>
                </table>
            </div>`;

        forecastResult.innerHTML += tableHTML;
    }
}

});

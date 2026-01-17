document.addEventListener('DOMContentLoaded', () => {
    const datasetName = new URLSearchParams(window.location.search).get('dataset_name');
    const edaForm = document.getElementById("eda-form");
    const edaResult = document.getElementById("eda-result");

    // Set dataset_name to hidden input field dynamically
    const datasetInput = document.getElementById('dataset_name');
    datasetInput.value = datasetName;

    // Optional: Show dataset name on page header if you have an element for that
    const datasetNameSpan = document.getElementById('dataset-name');
    if (datasetNameSpan) datasetNameSpan.innerText = datasetName;

    edaForm.addEventListener("submit", function (e) {
        e.preventDefault(); // Prevent page reload

        const formData = new FormData(edaForm);
        const params = new URLSearchParams();

        // Convert form data to URL-encoded format
        formData.forEach((value, key) => params.append(key, value));

        console.log("Sending EDA Request:", params.toString());

        // Clear previous results and show loading message
        edaResult.innerHTML = "<p>Running EDA analysis...</p>";

        fetch("/eda", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: params.toString()
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json(); // Expect JSON response
        })
        .then(data => {
            console.log("EDA Response:", data);

            // Clear existing content
            edaResult.innerHTML = "";

            // If there's an error key in response, show it
            if (data.error) {
                edaResult.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
                return;
            }

            // Dynamically render available plots
            const plotTitles = {
                "time_series": "Time Series Plot",
                "trend_seasonality": "Trend & Seasonality",
                "moving_avg": "Moving Average",
                "heatmap": "Heatmap",
                "autocorrelation": "Autocorrelation Plot"
            };

            for (const [key, title] of Object.entries(plotTitles)) {
                if (data[key]) {
                    const section = document.createElement("div");
                    section.innerHTML = `
                        <h3>${title}</h3>
                        <img src="${data[key]}" alt="${title}" style="max-width: 100%; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    `;
                    edaResult.appendChild(section);
                }
            }

            // Handle ADF test result (if present)
            if (data.adf_test) {
                const adfSection = document.createElement("div");
                adfSection.innerHTML = `
                    <h3>Stationarity Test (ADF)</h3>
                    <p><strong>p-value:</strong> ${data.adf_test.p_value}</p>
                    <p><strong>Conclusion:</strong> ${data.adf_test.stationarity}</p>
                `;
                edaResult.appendChild(adfSection);
            }

            // If nothing found
            if (edaResult.innerHTML.trim() === "") {
                edaResult.innerHTML = "<p>No visualizations returned.</p>";
            }

        })
        .catch(error => {
            console.error("EDA Fetch Error:", error);
            edaResult.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const datasetName = new URLSearchParams(window.location.search).get('dataset_name');
    const evaluateForm = document.getElementById("evaluate-form");
    const evaluateResult = document.getElementById("evaluate-result");

    // Dynamically inject dataset name into hidden input
    const datasetInput = document.getElementById('dataset_name');
    datasetInput.value = datasetName;

    // Optional: Display dataset name in the heading if element exists
    const datasetNameSpan = document.getElementById('dataset-name');
    if (datasetNameSpan) datasetNameSpan.innerText = datasetName;

    evaluateForm.addEventListener("submit", function (e) {
        e.preventDefault(); // Prevent form from submitting traditionally

        const formData = new FormData(evaluateForm);
        const params = new URLSearchParams();

        formData.forEach((value, key) => params.append(key, value));

        console.log("Sending Model Evaluation Request:", params.toString());

        evaluateResult.innerHTML = "<p>Evaluating models...</p>";

        fetch("/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: params.toString()
        })
            .then(response => response.json())
            .then(data => {
                console.log("Model Evaluation Response:", data);
                evaluateResult.innerHTML = ""; // Clear previous content

                const title = document.createElement("h3");
                title.innerText = "Model Ranking & Evaluation";
                evaluateResult.appendChild(title);

                const rankedModels = data.ranked_models;

                // Handle empty or missing results
                if (!rankedModels || rankedModels.length === 0) {
                    evaluateResult.innerHTML += "<p>No ranking data available.</p>";
                    return;
                }

                // Create ranked list
                const ol = document.createElement("ol");

                rankedModels.forEach(([modelName, metrics]) => {
                    const li = document.createElement("li");
                    li.classList.add('result-card'); // Consistent card styling

                    const modelTitle = document.createElement("h4");
                    modelTitle.innerText = `${modelName}`;
                    li.appendChild(modelTitle);

                    // Error display
                    if (metrics.error) {
                        const errorMsg = document.createElement("p");
                        errorMsg.innerHTML = `<strong>Error:</strong> ${metrics.error}`;
                        errorMsg.style.color = "red";
                        li.appendChild(errorMsg);
                    }
                    // Metrics display
                    else {
                        const metricsList = document.createElement("ul");
                        metricsList.innerHTML = `
                            <li><strong>MAE:</strong> ${metrics.MAE.toFixed(4)}</li>
                            <li><strong>RMSE:</strong> ${metrics.RMSE.toFixed(4)}</li>
                            <li><strong>MAPE:</strong> ${(metrics.MAPE * 100).toFixed(2)}%</li>
                        `;
                        li.appendChild(metricsList);
                    }

                    ol.appendChild(li);
                });

                evaluateResult.appendChild(ol);
            })
            .catch(error => {
                console.error("Model Evaluation Fetch Error:", error);
                evaluateResult.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
            });
    });
});

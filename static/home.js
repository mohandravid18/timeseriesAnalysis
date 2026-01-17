document.addEventListener("DOMContentLoaded", function () {
    const fetchForm = document.getElementById("fetch-form");
    const fetchResult = document.getElementById("fetch-result");
    const datasetList = document.getElementById("dataset-list");

    // Fetch list of datasets on page load
    fetch("/list_datasets")
        .then(response => response.json())
        .then(data => {
            datasetList.innerHTML = ""; // Clear loading message

            if (data.datasets.length === 0) {
                datasetList.innerHTML = "<p>No datasets found. Please fetch data from API to get started.</p>";
            } else {
                data.datasets.forEach(name => {
                    const btn = document.createElement("button");
                    btn.innerText = `${name}`;
                    btn.onclick = () => window.location.href = `/app?dataset_name=${encodeURIComponent(name)}`;
                    btn.className = "dataset-btn";
                    datasetList.appendChild(btn);
                });
            }
        })
        .catch(err => {
            datasetList.innerHTML = "<p style='color:red;'>Failed to load datasets. Please try again later.</p>";
            console.error("Dataset Fetch Error:", err);
        });

    // Handle Fetch Data Form
    fetchForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const formData = new FormData(fetchForm);
        const params = new URLSearchParams();
        formData.forEach((v, k) => params.append(k, v));

        fetchResult.innerText = "Fetching data, please wait...";
        fetch("/fetch", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: params.toString()
        })
            .then(res => res.json())
            .then(data => {
                fetchResult.innerText = JSON.stringify(data, null, 2);

                // Optional: Reload dataset list after successful fetch
                if (data.message === "Data fetched successfully!") {
                    setTimeout(() => location.reload(), 2000); // Reload to show new dataset
                }
            })
            .catch(err => fetchResult.innerText = "Error: " + err.message);
    });
});

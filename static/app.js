document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const datasetName = urlParams.get('dataset_name');
    document.getElementById('dataset-name').innerText = datasetName;

    document.getElementById('eda-link').href = `/eda_page?dataset_name=${datasetName}`;
    document.getElementById('forecast-link').href = `/forecast_page?dataset_name=${datasetName}`;
    document.getElementById('evaluate-link').href = `/evaluate_page?dataset_name=${datasetName}`;
    document.getElementById('view-link').href = `/view_table?dataset_name=${datasetName}`;
});

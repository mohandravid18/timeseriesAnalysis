document.addEventListener('DOMContentLoaded', () => {
    const datasetName = new URLSearchParams(window.location.search).get('dataset_name');
    const tableResult = document.getElementById('table-result');
    const datasetNameSpan = document.getElementById('dataset-name');

    // Display dataset name in header
    if (datasetNameSpan) datasetNameSpan.innerText = datasetName;

    console.log(`Loading dataset: ${datasetName}`);

    // Fetch JSON dataset properly
    fetch(`/api/get_dataset?dataset_name=${datasetName}`) // Correct API endpoint
        .then(response => {
            if (!response.ok) throw new Error(`Failed to load dataset. Status: ${response.status}`);
            return response.json(); // Expect JSON
        })
        .then(data => {
            console.log("Dataset Loaded Successfully:", data);

            const { keys, rows } = data;

            if (!keys.length || !rows.length) {
                tableResult.innerHTML = "<p>No data found for this dataset.</p>";
                return;
            }

            // Dynamically create table
            const table = document.createElement('table');

            // Create header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            keys.forEach(key => {
                const th = document.createElement('th');
                th.textContent = key;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create body
            const tbody = document.createElement('tbody');
            rows.forEach(row => {
                const tr = document.createElement('tr');
                keys.forEach(key => {
                    const td = document.createElement('td');
                    td.textContent = row[key] !== undefined ? row[key] : '';
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);

            // Render table
            tableResult.innerHTML = "";
            tableResult.appendChild(table);
        })
        .catch(error => {
            console.error("Error loading dataset table:", error);
            tableResult.innerHTML = `<p style="color: red;">Failed to load dataset: ${error.message}</p>`;
        });
});


async function consultarUsoOpenAI() {
    const email = document.getElementById("emailStats").value;
    const desde = document.getElementById("desdeStats").value;
    const hasta = document.getElementById("hastaStats").value;

    const params = new URLSearchParams({ user_email: email });
    if (desde) params.append("desde", desde);
    if (hasta) params.append("hasta", hasta);

    const response = await fetch(`/uso-openai?${params.toString()}`);
    const data = await response.json();

    const contenedor = document.getElementById("resultadoStats");
    contenedor.innerHTML = "";

    if (data.error) {
        contenedor.innerHTML = "<p style='color:red'>" + data.error + "</p>";
        return;
    }

    if (data.uso.length === 0) {
        contenedor.innerHTML = "<p>No se encontraron registros.</p>";
        return;
    }

    const tabla = document.createElement("table");
    tabla.border = "1";
    tabla.innerHTML = `
        <tr>
            <th>Modelo</th>
            <th>Tipo de Consulta</th>
            <th>Cantidad</th>
            <th>Prompt Tokens</th>
            <th>Completion Tokens</th>
            <th>Total Tokens</th>
        </tr>
    `;

    data.uso.forEach(item => {
        const fila = document.createElement("tr");
        fila.innerHTML = `
            <td>${item.modelo}</td>
            <td>${item.tipo_consulta}</td>
            <td>${item.cantidad}</td>
            <td>${item.prompt_tokens}</td>
            <td>${item.completion_tokens}</td>
            <td>${item.total_tokens}</td>
        `;
        tabla.appendChild(fila);
    });

    contenedor.appendChild(tabla);
}

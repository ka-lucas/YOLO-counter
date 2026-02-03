document.addEventListener("DOMContentLoaded", () => {

  /* =============================
     TROCA DE ABAS
  ============================== */
  const tabs = document.querySelectorAll(".config-tab");
  const sections = document.querySelectorAll(".config-section");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;

      tabs.forEach(t => t.classList.remove("active"));
      sections.forEach(s => s.classList.remove("active"));

      tab.classList.add("active");
      document.getElementById(`tab-${target}`)?.classList.add("active");
    });
  });

  /* =============================
     MODELO IA — CONFIANÇA
  ============================== */
  const confidenceRange = document.getElementById("confidenceRange");
  const confidenceValue = document.getElementById("confidenceValue");

  if (confidenceRange && confidenceValue) {
    confidenceValue.textContent = `${confidenceRange.value}%`;
    confidenceRange.addEventListener("input", () => {
      confidenceValue.textContent = `${confidenceRange.value}%`;
    });
  }

  /* =============================
     LINHA VIRTUAL — PREVIEW
  ============================== */
  const lineRange = document.getElementById("linePositionRange");
  const lineValue = document.getElementById("linePositionValue");
  const lineThickness = document.getElementById("lineThickness");
  const lineColor = document.getElementById("lineColor");
  const previewLine = document.getElementById("previewLine");

  // segurança: só executa se existir
  if (lineRange && lineValue && lineThickness && lineColor && previewLine) {

    function updatePreview() {
  const position = Number(lineRange.value);
  const thickness = Number(lineThickness.value);
  const color = lineColor.value;

  const previewArea = previewLine.parentElement;
  const previewHeight = previewArea.clientHeight;

  // calcula posição real em pixels
  const topPx = (position / 100) * previewHeight;

  // aplica estilos
  previewLine.style.top = `${topPx}px`;
  previewLine.style.height = `${thickness}px`;
  previewLine.style.backgroundColor = color;

  // atualiza label
  lineValue.textContent = `${position}%`;
}


    // eventos
    lineRange.addEventListener("input", updatePreview);
    lineThickness.addEventListener("change", updatePreview);
    lineColor.addEventListener("input", updatePreview);

    // estado inicial
    updatePreview();
  }

});

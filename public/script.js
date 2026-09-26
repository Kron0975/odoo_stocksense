let products = [];
let editingId = null;

const rows = document.getElementById("productRows");
const empty = document.getElementById("emptyState");
const searchInput = document.getElementById("searchInput");
const deliveryPreview = document.getElementById("deliveryPreview");

async function loadProducts() {
  const response = await fetch("/api/products");
  products = await response.json();
  renderProducts();
}

function renderProducts() {
  const term = searchInput.value.trim().toLowerCase();

  const filtered = products.filter(product =>
    product.name.toLowerCase().includes(term) ||
    product.sku.toLowerCase().includes(term)
  );

  rows.innerHTML = "";

  empty.classList.toggle("hidden", filtered.length > 0);

  filtered.forEach(product => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><strong>[${product.sku}] ${product.name}</strong></td>
      <td>${product.unitCost.toLocaleString("en-IN")} Rs</td>
      <td>${product.onHand}</td>
      <td>${product.freeToUse}</td>
      <td><button class="update-link" data-id="${product.id}">Update</button></td>
    `;

    rows.appendChild(tr);
  });
}

function openModal(product) {
  editingId = product.id;
  document.getElementById("modalTitle").textContent =
    `Update Stock — ${product.name}`;
  document.getElementById("onHand").value = product.onHand;
  document.getElementById("freeToUse").value = product.freeToUse;
  document.getElementById("formError").textContent = "";
  document.getElementById("stockModal").classList.remove("hidden");
}

function closeModal() {
  editingId = null;
  document.getElementById("stockModal").classList.add("hidden");
}

rows.addEventListener("click", event => {
  const button = event.target.closest(".update-link");
  if (!button) return;

  const product = products.find(p => p.id === Number(button.dataset.id));
  if (product) openModal(product);
});

document.getElementById("stockForm").addEventListener("submit", async event => {
  event.preventDefault();

  const onHand = Number(document.getElementById("onHand").value);
  const freeToUse = Number(document.getElementById("freeToUse").value);
  const error = document.getElementById("formError");

  if (freeToUse > onHand) {
    error.textContent = "Free to Use cannot be greater than On Hand.";
    return;
  }

  const response = await fetch(`/api/products/${editingId}/stock`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ onHand, freeToUse })
  });

  const data = await response.json();

  if (!response.ok) {
    error.textContent = data.message || "Unable to update stock.";
    return;
  }

  await loadProducts();
  closeModal();
});

document.getElementById("searchButton").addEventListener("click", () => {
  document.getElementById("searchBox").classList.toggle("hidden");
  if (!document.getElementById("searchBox").classList.contains("hidden")) {
    searchInput.focus();
  }
});

searchInput.addEventListener("input", renderProducts);

document.getElementById("closeModal").addEventListener("click", closeModal);
document.getElementById("cancelModal").addEventListener("click", closeModal);

document.getElementById("operationsBtn").addEventListener("click", () => {
  document.getElementById("operationsMenu").classList.toggle("hidden");
});

document.getElementById("deliveryOption").addEventListener("click", () => {
  document.getElementById("operationsMenu").classList.add("hidden");
  deliveryPreview.classList.remove("hidden");
  deliveryPreview.scrollIntoView({ behavior: "smooth" });
});

document.addEventListener("click", event => {
  if (!event.target.closest(".nav-group")) {
    document.getElementById("operationsMenu").classList.add("hidden");
  }
});

loadProducts();

let products = [];
let currentProductId = null;

// ===============================
// LOAD PRODUCTS
// ===============================

async function loadProducts() {
  try {
    const response = await fetch("/api/products");

    if (!response.ok) {
      throw new Error("Failed to load products");
    }

    products = await response.json();

    renderProducts(products);

  } catch (error) {
    console.error(error);

    document.getElementById("productRows").innerHTML = `
      <tr>
        <td colspan="6" class="error">
          Unable to load stock data.
        </td>
      </tr>
    `;
  }
}


// ===============================
// RENDER PRODUCTS
// ===============================

function renderProducts(list) {

  const rows = document.getElementById("productRows");
  const emptyState = document.getElementById("emptyState");

  rows.innerHTML = "";

  if (!list || list.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");

  list.forEach(product => {

    const row = document.createElement("tr");

    const onHand = Number(product.onHand || 0);
    const freeToUse = Number(product.freeToUse || 0);
    const reorderLevel = Number(product.reorderLevel || 0);

    let statusText = "In Stock";
    let statusClass = "status-in-stock";

    if (onHand <= 0) {
      statusText = "Out of Stock";
      statusClass = "status-out-stock";
    } else if (reorderLevel > 0 && onHand <= reorderLevel) {
      statusText = "Low Stock";
      statusClass = "status-low-stock";
    }

    row.innerHTML = `
      <td>
        <div class="product-name">
          ${escapeHtml(product.name || "Unnamed Product")}
        </div>

        <div class="product-sku">
          [${escapeHtml(product.sku || "N/A")}]
        </div>
      </td>

      <td>
        ₹${Number(product.unitCost || 0).toLocaleString("en-IN")}
      </td>

      <td>
        <strong>${onHand}</strong>
      </td>

      <td>
        ${freeToUse}
      </td>

      <td>
        <span class="stock-status ${statusClass}">
          ${statusText}
        </span>
      </td>

      <td>
        <button
          class="update-button"
          data-id="${product.id}"
        >
          Update
        </button>
      </td>
    `;

    rows.appendChild(row);
  });

  document.querySelectorAll(".update-button").forEach(button => {

    button.addEventListener("click", () => {
      openStockModal(button.dataset.id);
    });

  });
}


// ===============================
// SEARCH
// ===============================

const searchButton = document.getElementById("searchButton");
const searchBox = document.getElementById("searchBox");
const searchInput = document.getElementById("searchInput");

searchButton.addEventListener("click", () => {

  searchBox.classList.toggle("hidden");

  if (!searchBox.classList.contains("hidden")) {
    searchInput.focus();
  } else {
    searchInput.value = "";
    renderProducts(products);
  }

});


searchInput.addEventListener("input", () => {

  const searchTerm = searchInput.value
    .trim()
    .toLowerCase();

  if (!searchTerm) {
    renderProducts(products);
    return;
  }

  const filteredProducts = products.filter(product => {

    const name = String(product.name || "").toLowerCase();
    const sku = String(product.sku || "").toLowerCase();

    return (
      name.includes(searchTerm) ||
      sku.includes(searchTerm)
    );

  });

  renderProducts(filteredProducts);

});


// ===============================
// STOCK MODAL
// ===============================

const stockModal = document.getElementById("stockModal");
const stockForm = document.getElementById("stockForm");
const modalTitle = document.getElementById("modalTitle");
const onHandInput = document.getElementById("onHand");
const freeToUseInput = document.getElementById("freeToUse");
const formError = document.getElementById("formError");


function openStockModal(productId) {

  const product = products.find(
    item => String(item.id) === String(productId)
  );

  if (!product) {
    console.error("Product not found:", productId);
    return;
  }

  currentProductId = product.id;

  modalTitle.textContent =
    `Update Stock — ${product.name}`;

  onHandInput.value = product.onHand ?? 0;
  freeToUseInput.value = product.freeToUse ?? 0;

  formError.textContent = "";

  stockModal.classList.remove("hidden");

  setTimeout(() => {
    onHandInput.focus();
  }, 50);
}


// ===============================
// CLOSE MODAL
// ===============================

function closeStockModal() {

  stockModal.classList.add("hidden");

  currentProductId = null;

  formError.textContent = "";
}


document
  .getElementById("closeModal")
  .addEventListener("click", closeStockModal);


document
  .getElementById("cancelModal")
  .addEventListener("click", closeStockModal);


// ===============================
// UPDATE STOCK
// ===============================

stockForm.addEventListener("submit", async event => {

  event.preventDefault();

  formError.textContent = "";

  const onHand = Number(onHandInput.value);
  const freeToUse = Number(freeToUseInput.value);

  if (!Number.isFinite(onHand) || !Number.isFinite(freeToUse)) {
    formError.textContent =
      "Please enter valid stock quantities.";
    return;
  }

  if (onHand < 0 || freeToUse < 0) {
    formError.textContent =
      "Stock quantities cannot be negative.";
    return;
  }

  if (freeToUse > onHand) {
    formError.textContent =
      "Free to Use cannot be greater than On Hand.";
    return;
  }

  try {

    const response = await fetch(
      `/api/products/${currentProductId}/stock`,
      {
        method: "PUT",

        headers: {
          "Content-Type": "application/json"
        },

        body: JSON.stringify({
          onHand,
          freeToUse
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.message || "Unable to update stock."
      );
    }

    /*
      The API may return the updated product
      directly OR inside data.product.
    */

    const updatedProduct =
      data.product || data;

    const productIndex = products.findIndex(
      product =>
        String(product.id) ===
        String(currentProductId)
    );

    if (productIndex !== -1 && updatedProduct) {
      products[productIndex] = updatedProduct;
    }

    renderProducts(products);

    closeStockModal();

    showNotification(
      "Stock updated successfully."
    );

  } catch (error) {

    console.error(error);

    formError.textContent =
      error.message ||
      "Unable to update stock.";

  }

});


// ===============================
// SUCCESS NOTIFICATION
// ===============================

function showNotification(message) {

  const notification =
    document.createElement("div");

  notification.className =
    "stock-notification";

  notification.textContent =
    message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  setTimeout(() => {

    notification.classList.remove("show");

    setTimeout(() => {
      notification.remove();
    }, 300);

  }, 2500);
}


// ===============================
// OPERATIONS DROPDOWN
// ===============================

const operationsBtn =
  document.getElementById("operationsBtn");

const operationsMenu =
  document.getElementById("operationsMenu");


operationsBtn.addEventListener("click", event => {

  event.stopPropagation();

  operationsMenu.classList.toggle("hidden");

});


document.addEventListener("click", () => {

  operationsMenu.classList.add("hidden");

});


operationsMenu.addEventListener("click", event => {

  event.stopPropagation();

});


// ===============================
// DELIVERY PREVIEW
// ===============================

const deliveryOption =
  document.getElementById("deliveryOption");

const deliveryPreview =
  document.getElementById("deliveryPreview");


deliveryOption.addEventListener("click", () => {

  deliveryPreview.classList.remove("hidden");

  operationsMenu.classList.add("hidden");

  deliveryPreview.scrollIntoView({
    behavior: "smooth"
  });

});


// ===============================
// HTML ESCAPE
// ===============================

function escapeHtml(value) {

  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

}


// ===============================
// INITIAL LOAD
// ===============================

loadProducts();
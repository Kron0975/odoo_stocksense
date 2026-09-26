const express = require("express");
const path = require("path");

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// Hour 1 seed data. Later milestones will move this into persistent storage.
let products = [
  {
    id: 1,
    name: "Desk",
    sku: "DESK001",
    category: "Furniture",
    unit: "Unit",
    unitCost: 3000,
    onHand: 50,
    freeToUse: 45,
    location: "WH/Stock1",
    reorderLevel: 10,
    reorderQuantity: 20
  },
  {
    id: 2,
    name: "Table",
    sku: "TABLE001",
    category: "Furniture",
    unit: "Unit",
    unitCost: 3000,
    onHand: 50,
    freeToUse: 50,
    location: "WH/Stock1",
    reorderLevel: 10,
    reorderQuantity: 20
  }
];

// GET all products
app.get("/api/products", (req, res) => {
  res.json(products);
});

// GET one product
app.get("/api/products/:id", (req, res) => {
  const product = products.find(p => p.id === Number(req.params.id));

  if (!product) {
    return res.status(404).json({ message: "Product not found" });
  }

  res.json(product);
});

// UPDATE stock - used by the Stock screen
app.put("/api/products/:id/stock", (req, res) => {
  const product = products.find(p => p.id === Number(req.params.id));

  if (!product) {
    return res.status(404).json({ message: "Product not found" });
  }

  const onHand = Number(req.body.onHand);
  const freeToUse = Number(req.body.freeToUse);

  if (
    !Number.isFinite(onHand) ||
    !Number.isFinite(freeToUse) ||
    onHand < 0 ||
    freeToUse < 0 ||
    freeToUse > onHand
  ) {
    return res.status(400).json({
      message: "Invalid stock values. Free to Use cannot exceed On Hand."
    });
  }

  product.onHand = onHand;
  product.freeToUse = freeToUse;

  res.json(product);
});

app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, () => {
  console.log(`StockSense running at http://localhost:${PORT}`);
});

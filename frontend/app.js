const API = "http://localhost:8000";
const productList = document.querySelector("#productList");
const chatHistory = [];

function renderProducts(products) {
  productList.innerHTML = products.length
    ? products.map(p => `<article class="card"><h3>${escapeHtml(p.TenSP)}</h3>
      <p>${escapeHtml(p.DanhMuc || "")} · ${escapeHtml(p.ThuongHieu || "Chưa cập nhật thương hiệu")}</p>
      <p class="price">${Number(p.GiaBan).toLocaleString("vi-VN")} đồng</p>
      <p>${p.SoLuongTon > 0 ? "Còn hàng" : "Hết hàng"}</p></article>`).join("")
    : "<p>Không tìm thấy sản phẩm tương ứng trong siêu thị.</p>";
}

async function searchProducts() {
  const keyword = document.querySelector("#keyword").value.trim();
  const response = await fetch(`${API}/api/products?keyword=${encodeURIComponent(keyword)}`);
  if (!response.ok) throw new Error("Không thể tìm sản phẩm.");
  renderProducts(await response.json());
}

document.querySelector("#searchButton").addEventListener("click", () => searchProducts().catch(e => alert(e.message)));
document.querySelector("#imageFile").addEventListener("change", async (event) => {
  const file = event.target.files[0]; if (!file) return;
  const status = document.querySelector("#imageStatus"); status.textContent = "Đang tìm ảnh tương tự...";
  const form = new FormData(); form.append("file", file);
  try {
    const response = await fetch(`${API}/api/image-search`, { method:"POST", body:form });
    const data = await response.json(); if (!response.ok) throw new Error(data.detail);
    renderProducts(data.products);
    status.textContent = data.products.length ? "Đã tìm thấy sản phẩm đang bán." : "Không có ánh xạ sản phẩm trong siêu thị.";
  } catch (error) { status.textContent = error.message; }
});

document.querySelector("#sendButton").addEventListener("click", async () => {
  const input = document.querySelector("#question"); const question = input.value.trim();
  if (!question) return;
  const messages = document.querySelector("#chatMessages");
  messages.insertAdjacentHTML("beforeend", `<p class="user">${question}</p>`); input.value = "";
  try {
    const response = await fetch(`${API}/api/chat`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({question, history:chatHistory.slice(-6)})
    });

    document.querySelector("#question").addEventListener("keydown", event => {
      if (event.key === "Enter") document.querySelector("#sendButton").click();
    });
    const data = await response.json(); if (!response.ok) throw new Error(data.detail);
    messages.insertAdjacentHTML("beforeend", `<p class="bot">${escapeHtml(data.answer).replaceAll("\n", "<br>")}</p>`);
    chatHistory.push({role:"user", content:question}, {role:"assistant", content:data.answer});
    if (data.products) renderProducts(data.products);
  } catch (error) { messages.insertAdjacentHTML("beforeend", `<p class="bot">${escapeHtml(error.message)}</p>`); }
});

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[char]));
}

const form = document.getElementById("contact-form");
const nameInput = document.getElementById("name");
const phoneInput = document.getElementById("phone");
const searchInput = document.getElementById("search");
const message = document.getElementById("message");
const list = document.getElementById("contact-list");

async function fetchContacts(query = "") {
  const response = await fetch(`/api/contacts?q=${encodeURIComponent(query)}`);
  const data = await response.json();
  renderContacts(data.contacts || []);
}

function renderContacts(contacts) {
  list.innerHTML = "";
  contacts.forEach((contact) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span><strong>${contact.name}</strong> - ${contact.phone}</span>
      <button class="delete-btn" data-name="${contact.name}">Delete</button>
    `;
    list.appendChild(li);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";

  const response = await fetch("/api/contacts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: nameInput.value, phone: phoneInput.value }),
  });

  const data = await response.json();
  if (!response.ok) {
    message.textContent = data.error || "Failed to add contact.";
    return;
  }

  message.textContent = "Contact added.";
  nameInput.value = "";
  phoneInput.value = "";
  fetchContacts(searchInput.value);
});

searchInput.addEventListener("input", () => {
  fetchContacts(searchInput.value);
});

list.addEventListener("click", async (event) => {
  if (!event.target.classList.contains("delete-btn")) {
    return;
  }
  const name = event.target.getAttribute("data-name");
  const response = await fetch("/api/contacts", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });

  if (response.ok) {
    fetchContacts(searchInput.value);
  }
});

fetchContacts();

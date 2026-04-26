const form = document.getElementById("contact-form");
const nameInput = document.getElementById("name");
const phoneInput = document.getElementById("phone");
const searchInput = document.getElementById("search");
const message = document.getElementById("message");
const list = document.getElementById("contact-list");

async function fetchContacts(query = "") {
  try {
    const response = await fetch(`/api/contacts?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      message.textContent = "Failed to load contacts.";
      return;
    }
    const data = await response.json();
    renderContacts(data.contacts || []);
    message.textContent = "";
  } catch (error) {
    message.textContent = "Network error while loading contacts.";
  }
}

function renderContacts(contacts) {
  list.innerHTML = "";
  contacts.forEach((contact) => {
    const li = document.createElement("li");
    const details = document.createElement("span");
    const strong = document.createElement("strong");
    strong.textContent = contact.name;
    details.appendChild(strong);
    details.appendChild(document.createTextNode(` - ${contact.phone}`));

    const button = document.createElement("button");
    button.className = "delete-btn";
    button.textContent = "Delete";
    button.setAttribute("data-name", contact.name);

    li.appendChild(details);
    li.appendChild(button);
    list.appendChild(li);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";

  try {
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
  } catch (error) {
    message.textContent = "Network error while adding contact.";
  }
});

searchInput.addEventListener("input", () => {
  fetchContacts(searchInput.value);
});

list.addEventListener("click", async (event) => {
  if (!event.target.classList.contains("delete-btn")) {
    return;
  }
  const name = event.target.getAttribute("data-name");
  try {
    const response = await fetch("/api/contacts", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    if (response.ok) {
      message.textContent = "";
      fetchContacts(searchInput.value);
    } else {
      message.textContent = "Failed to delete contact.";
    }
  } catch (error) {
    message.textContent = "Network error while deleting contact.";
  }
});

fetchContacts();

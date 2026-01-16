const API_URL = "https://placement-portal-zj38.onrender.com/api/students";

async function loadStudents() {
  try {
    const res = await fetch(API_URL);

    if (!res.ok) {
      throw new Error("Server responded with error");
    }

    const students = await res.json();

    // REMOVE ERROR ALERT
    alert("Backend connected successfully 🎉");

    const list = document.getElementById("studentList");
    list.innerHTML = "";

    students.forEach((s) => {
      const li = document.createElement("li");
      li.textContent = `${s.name} - ${s.branch}`;
      list.appendChild(li);
    });

  } catch (error) {
    alert("Backend not connected yet!");
    console.error(error);
  }
}

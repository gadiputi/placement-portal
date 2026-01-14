async function loadStudents() {
  try {
    // CHANGE THIS URL AFTER BACKEND IS DEPLOYED
    const response = await fetch("http://localhost:3000/api/students");
    const students = await response.json();

    const list = document.getElementById("studentList");
    list.innerHTML = "";

    students.forEach(student => {
      const li = document.createElement("li");
      li.textContent = `${student.name} - ${student.branch}`;
      list.appendChild(li);
    });
  } catch (error) {
    alert("Backend not connected yet!");
  }
}

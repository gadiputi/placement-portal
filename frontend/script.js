async function loadStudents() {
  try {
    const response = await fetch(
      "https://placement-portal-zj38.onrender.com/api/students"
    );

    if (!response.ok) {
      throw new Error("Backend not connected");
    }

    const students = await response.json();
    console.log(students);
    alert("Students loaded successfully 🎉");
  } catch (error) {
    alert("Backend not connected yet!");
    console.error(error);
  }
}

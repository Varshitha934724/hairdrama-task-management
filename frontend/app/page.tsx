"use client";

import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
);

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tasks, setTasks] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [assignedTo, setAssignedTo] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [dueTime, setDueTime] = useState("");

  useEffect(() => {
    checkUser();
  }, []);

  async function checkUser() {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    setUser(session?.user ?? null);
    setLoading(false);

    if (session?.user) {
      loadTasks();
      loadUsers();
    }
  }

 async function loadTasks() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const response = await fetch(
  "https://hairdrama-task-management.onrender.com/api/tasks",
    {
      headers: {
        Authorization: `Bearer ${session?.access_token}`,
      },
    }
  );

  const data = await response.json();

  if (data.success) {
    setTasks(data.tasks);
  }
}

  async function loadUsers() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

 const response = await fetch(
  "https://hairdrama-task-management.onrender.com/api/users",
    {
      headers: {
        Authorization: `Bearer ${session?.access_token}`,
      },
    }
  );

  const data = await response.json();

  if (data.success) {
    
    setUsers(data.users);
  }
}

  async function createTask() {
    
    if (!title.trim()) {
      alert("Please enter a task title");
      return;
    }

    

    const {
     data: { session },
    } = await supabase.auth.getSession();

    const accessToken = session?.access_token;
    
    const response = await fetch("https://hairdrama-task-management.onrender.com/api/tasks", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
     body: JSON.stringify({
      title: title,
      description: description,
      created_by: user.id,
      assigned_to: assignedTo || null,
      due_date: dueDate || null,
      due_time: dueTime || null,
      }),
    });

    const data = await response.json();

    if (data.success) {
      alert("Task created successfully! Email sent: " + data.email_sent);


      setTitle("");
      setDescription("");
      setAssignedTo("");
      setDueDate("");
      setDueTime("");

      setTitle("");
      setDescription("");

      loadTasks();
    } else {
      alert("Failed to create task:" +data.error);
    }
  }

  async function completeTask(taskId: string) {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const response = await fetch(
    `http://127.0.0.1:5000/api/tasks/${taskId}/complete`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${session?.access_token}`,
      },
    }
  );

  const data = await response.json();

  if (data.success) {
    alert("Task completed! Email sent: " + data.email_sent);
    loadTasks();
  } else {
    alert("Failed to complete task: " + data.error);
  }
}
 
 
  async function logout() {
    await supabase.auth.signOut();
    setUser(null);
  }

  if (loading) {
    return <main style={{ padding: "40px" }}>Loading...</main>;
  }

  if (!user) {
    return (
      <main style={{ padding: "40px" }}>
        <h1>Hairdrama Task Management</h1>

        <button
          onClick={async () => {
            await supabase.auth.signInWithOAuth({
              provider: "google",
              options: {
                redirectTo: "http://localhost:3000/auth/callback",
              },
            });
          }}
        >
          Continue with Google
        </button>
      </main>
    );
  }

  return (
    <main style={{ padding: "40px", maxWidth: "700px" }}>
      <h1>Hairdrama Task Management</h1>

      <p>
        Welcome, <strong>{user.email}</strong>
      </p>

      <button onClick={logout}>Logout</button>

      <hr style={{ margin: "30px 0" }} />

      <h2>Create Task</h2>

      <input
        type="text"
        placeholder="Task title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        style={{
          display: "block",
          width: "100%",
          padding: "10px",
          marginBottom: "10px",
          border: "1px solid #999",
          borderRadius: "5px",
          backgroundColor: "white",
          color: "black",
        }}
      />

      <textarea
        placeholder="Task description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        style={{
          display: "block",
          width: "100%",
          padding: "10px",
          marginBottom: "10px",
          minHeight: "100px",
          border: "1px solid #999",
          borderRadius: "5px",
          backgroundColor: "white",
          color: "black",
        }}
      />
    <input
  type="date"
  value={dueDate}
  onChange={(e) => setDueDate(e.target.value)}
  style={{
    display: "block",
    width: "100%",
    padding: "10px",
    marginBottom: "10px",
    border: "1px solid #999",
    borderRadius: "5px",
  }}
/>

<input
  type="time"
  value={dueTime}
  onChange={(e) => setDueTime(e.target.value)}
  style={{
    display: "block",
    width: "100%",
    padding: "10px",
    marginBottom: "10px",
    border: "1px solid #999",
    borderRadius: "5px",
  }}
/>
      <select
  value={assignedTo}
  onChange={(e) => setAssignedTo(e.target.value)}
  style={{
    display: "block",
    width: "100%",
    padding: "10px",
    marginBottom: "10px",
    border: "1px solid #999",
    borderRadius: "5px",
    backgroundColor: "white",
    color: "black",
  }}
>
  <option value="">Assign to...</option>

  {users.map((person) => (
    <option key={person.id} value={person.id}>
      {person.name || person.email}
    </option>
  ))}
</select>

      <button
        type="button"
        onClick={createTask}
        style={{
          display: "block",
          position: "relative",
          zIndex: 10,
          padding: "12px 24px",
          marginTop: "10px",
          cursor: "pointer",
          backgroundColor: "black",
          color: "white",
          border: "1px solid black",
          borderRadius: "6px",
       }}
>
       Create Task
     </button>

      <hr style={{ margin: "30px 0" }} />

      <h2>Tasks</h2>

      {tasks.length === 0 ? (
        <p>No tasks yet.</p>
      ) : (
        tasks.map((task) => (
          <div
            key={task.id}
            style={{
              border: "1px solid #ccc",
              padding: "15px",
              marginBottom: "10px",
            }}
          >
            <h3>{task.title}</h3>

            <p>{task.description}</p>

            <p>
              Status: <strong>{task.status}</strong>
            </p>
            {task.due_date && (
  <p>
    Due Date: <strong>{task.due_date}</strong>
  </p>
)}

{task.due_time && (
  <p>
    Due Time: <strong>{task.due_time}</strong>
  </p>
)}

{task.assigned_to && (
  <p>
    Assigned To:{" "}
    <strong>
      {users.find((person) => person.id === task.assigned_to)?.name ||
        users.find((person) => person.id === task.assigned_to)?.email ||
        "User"}
    </strong>
  </p>
)}
            {task.status === "pending" && (
              <button
                onClick={() => completeTask(task.id)}
                style={{
                  padding: "8px 15px",
                  marginTop: "5px",
                  cursor: "pointer",
             }}
  >
    Mark as Completed
  </button>
)}
          </div>
        ))
      )}
    </main>
  );
}

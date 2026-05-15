  function openEditModal(room) {
    document.getElementById('edit_classroom_name').value = room.Classroom_Name || '';
    document.getElementById('edit_building').value       = room.Building        || '';
    document.getElementById('edit_floor').value          = room.Floor           || '';
    document.getElementById('edit_capacity').value       = room.Capacity        || '';
    document.getElementById('editClassroomForm').action  =
      '/classrooms/edit/' + room.Classroom_ID;
    new bootstrap.Modal(document.getElementById('editClassroomModal')).show();
  }

  function openDeleteModal(id, name) {
    document.getElementById('deleteClassroomName').textContent = name;
    document.getElementById('deleteClassroomForm').action      = '/classrooms/delete/' + id;
    new bootstrap.Modal(document.getElementById('deleteClassroomModal')).show();
  }
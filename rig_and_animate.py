import bpy


def clear_debug_prints():
    """Remove any leftover weight/debug print statements from text blocks."""
    for text in list(bpy.data.texts):
        if "weight" in text.name.lower() or "debug" in text.name.lower():
            lines = [ln for ln in text.as_string().splitlines()
                     if "print" not in ln.lower() or "weight" not in ln.lower()]
            text.clear()
            for ln in lines:
                text.write(ln + "\n")


def import_reference(filepath="assassin_reference.glb"):
    bpy.ops.import_scene.gltf(filepath=filepath)
    armature = next((o for o in bpy.context.selected_objects if o.type == "ARMATURE"), None)
    mesh = next((o for o in bpy.context.selected_objects if o.type == "MESH"), None)
    return armature, mesh


def redo_rig(armature):
    """Rebuild clean deform-bone names and keep the existing skin weights intact."""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in armature.data.edit_bones:
        if bone.name.startswith("mixamorig:"):
            bone.name = bone.name.replace("mixamorig:", "")
    bpy.ops.object.mode_set(mode="OBJECT")
    return armature


def motion_animate(armature, mesh):
    """Create a simple walk-cycle action on the rebuilt rig."""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")

    action = bpy.data.actions.new(name="WalkCycle")
    armature.animation_data_create()
    armature.animation_data.action = action

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 24

    def key(bone_name, rotation, frame):
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            return
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = rotation
        pose_bone.keyframe_insert("rotation_euler", frame=frame)

    # Hips bob
    for f, dz in [(1, 0.0), (7, -0.03), (13, 0.0), (19, -0.03)]:
        hips = armature.pose.bones.get("Hips")
        if hips:
            hips.location = (0, 0, dz)
            hips.keyframe_insert("location", frame=f)

    # Legs swing (opposite phases)
    for f in range(1, 25):
        phase = (f / 24.0) * 6.283
        import math
        thigh = math.sin(phase) * 0.5
        knee = max(0.0, -math.cos(phase)) * 0.8
        key("LeftUpLeg", (thigh, 0, 0), f)
        key("LeftLeg", (knee, 0, 0), f)
        key("RightUpLeg", (-thigh, 0, 0), f)
        key("RightLeg", (max(0.0, math.cos(phase)) * 0.8, 0, 0), f)

    # Arms counter-swing
    for f in range(1, 25):
        phase = (f / 24.0) * 6.283
        import math
        swing = math.sin(phase) * 0.35
        key("LeftUpperArm", (-swing, 0, 0), f)
        key("RightUpperArm", (swing, 0, 0), f)

    bpy.ops.object.mode_set(mode="OBJECT")

    # Make sure skin modifier still binds the mesh to the renamed rig
    if mesh:
        mod = next((m for m in mesh.modifiers if m.type == "SKIN"), None)
        if mod:
            mod.object = armature


def main():
    clear_debug_prints()
    armature, mesh = import_reference()
    redo_rig(armature)
    motion_animate(armature, mesh)


if __name__ == "__main__":
    main()

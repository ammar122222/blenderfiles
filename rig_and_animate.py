import bpy
import math


def strip_weight_debug_lines():
    """Delete any weight/debug logging lines left inside Blender text blocks."""
    for text in list(bpy.data.texts):
        kept = []
        for line in text.as_string().splitlines():
            low = line.lower()
            if "print" in low and ("weight" in low or "debug" in low):
                continue
            kept.append(line)
        if len(kept) != len(text.as_string().splitlines()):
            text.clear()
            for line in kept:
                text.write(line + "\n")


def import_reference(filepath="assassin_reference.glb"):
    bpy.ops.import_scene.gltf(filepath=filepath)
    armature = next((o for o in bpy.context.selected_objects if o.type == "ARMATURE"), None)
    mesh = next((o for o in bpy.context.selected_objects if o.type == "MESH"), None)
    return armature, mesh


def redo_rig(armature):
    """Rebuild clean deform-bone names and keep the existing skin weights intact.

    Bone names live in the Armature object's data, so renaming them does NOT
    affect vertex-group (weight) binding - vgroups are re-linked by name after
    each rename to guarantee the skin stays bound.
    """
    mesh_obj = next((o for o in bpy.data.objects
                     if o.type == "MESH" and o.parent == armature), None)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in list(armature.data.edit_bones):
        if bone.name.startswith("mixamorig:"):
            old = bone.name
            new = old.replace("mixamorig:", "")
            bone.name = new
            # Keep vertex-group weights linked to the renamed bone
            if mesh_obj and old in mesh_obj.vertex_groups:
                mesh_obj.vertex_groups[old].name = new
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
        thigh = math.sin(phase) * 0.5
        knee = max(0.0, -math.cos(phase)) * 0.8
        key("LeftUpLeg", (thigh, 0, 0), f)
        key("LeftLeg", (knee, 0, 0), f)
        key("RightUpLeg", (-thigh, 0, 0), f)
        key("RightLeg", (max(0.0, math.cos(phase)) * 0.8, 0, 0), f)

    # Arms counter-swing
    for f in range(1, 25):
        phase = (f / 24.0) * 6.283
        swing = math.sin(phase) * 0.35
        key("LeftUpperArm", (-swing, 0, 0), f)
        key("RightUpperArm", (swing, 0, 0), f)

    bpy.ops.object.mode_set(mode="OBJECT")

    # Make sure the Armature (SKELETAL) modifier still binds the mesh to the rig
    if mesh:
        mod = next((m for m in mesh.modifiers if m.type == "ARMATURE"), None)
        if mod is None:
            mod = mesh.modifiers.new(name="Armature", type="ARMATURE")
        mod.object = armature


def main():
    strip_weight_debug_lines()
    armature, mesh = import_reference()
    redo_rig(armature)
    motion_animate(armature, mesh)


if __name__ == "__main__":
    main()


import os
def save_annotations(data, output_dir, subject_name, verbose=True):
    """
    Save annotations to file.
    Constructs filename based on subject name and fixed suffix.
    """
    filename = f"{subject_name}_annotations.csv"
    save_path = os.path.join(output_dir, filename)
    
    if verbose:
        print(f"Saving annotations to {save_path}")
        
    data.annotations.save(save_path, overwrite=True)
    return save_path

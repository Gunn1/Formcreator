import matplotlib.pyplot as plt
import numpy as np

def generate_shape(shape_type, **kwargs):
    """
    Generates and plots a specified shape using Matplotlib.

    Args:
        shape_type (str): The type of shape to generate. 
                          Supported shapes: 'circle', 'square', 'triangle', 'polygon', 'star', 'custom'
        **kwargs: 
            - For 'circle': radius (float)
            - For 'square': side_length (float)
            - For 'triangle': base (float), height (float) 
            - For 'polygon': vertices (list of tuples)
            - For 'star': num_points (int), inner_radius (float), outer_radius (float)
            - For 'custom': path (list of tuples representing x,y coordinates)

    Returns:
        None
    """

    fig, ax = plt.subplots()

    if shape_type == 'circle':
        radius = kwargs.pop('radius', 1)  # Remove radius from kwargs
        circle = plt.Circle((0, 0), radius, **kwargs)  # Pass remaining kwargs
        ax.add_patch(circle)

    elif shape_type == 'square':
        side_length = kwargs.pop('side_length', 1)  # Remove side_length from kwargs
        x = -side_length / 2  # Calculate x-coordinate of bottom-left corner
        y = -side_length / 2  # Calculate y-coordinate of bottom-left corner
        rect = plt.Rectangle((x, y), side_length, side_length, **kwargs)  # Pass remaining kwargs
        ax.add_patch(rect)

    elif shape_type == 'triangle':
        base = kwargs.pop('base', 1)  # Remove base from kwargs
        height = kwargs.pop('height', 1)  # Remove height from kwargs
        triangle_coords = [(0, 0), (base/2, height), (base, 0)]
        triangle = plt.Polygon(triangle_coords, **kwargs)
        ax.add_patch(triangle)

    elif shape_type == 'polygon':
        vertices = kwargs.pop('vertices', [(0, 0), (1, 0), (0.5, 1)])  # Remove vertices from kwargs
        polygon = plt.Polygon(vertices, **kwargs)
        ax.add_patch(polygon)

    elif shape_type == 'star':
        num_points = kwargs.pop('num_points', 5)  # Remove num_points from kwargs
        inner_radius = kwargs.pop('inner_radius', 0.3)  # Remove inner_radius from kwargs
        outer_radius = kwargs.pop('outer_radius', 1)  # Remove outer_radius from kwargs
        star_coords = []
        for i in range(num_points * 2):
            r = outer_radius if i % 2 == 0 else inner_radius
            angle = np.pi * i / num_points
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            star_coords.append((x, y))
        star = plt.Polygon(star_coords, **kwargs)
        ax.add_patch(star)

    elif shape_type == 'custom':
        path = kwargs.pop('path', [(0, 0), (1, 0), (1, 1), (0, 1)])  # Remove path from kwargs
        polygon = plt.Polygon(path, **kwargs)
        ax.add_patch(polygon)

    else:
        print(f"Unsupported shape type: {shape_type}")
        return

    # Adjust plot limits to fit the shape
    ax.autoscale() 

    # Set equal aspect ratio for proper circle rendering
    ax.set_aspect('equal') 

    # Turn off axis
    ax.axis('off') 

    # Save the plot as a JPG image
    plt.savefig(f"{shape_type}.jpg", bbox_inches='tight', pad_inches=0) 
    plt.close()  # Close the plot to avoid multiple windows

def test_generate_shape():
    """
    Tests the generate_shape function with various shapes and parameters.
    """
    generate_shape('circle', radius=0.8, color='red')  
    generate_shape('square', side_length=1.2, color='green', fill=False)
    generate_shape('triangle', base=1.5, height=1, color='blue', alpha=0.5)
    generate_shape('polygon', vertices=[(0, 0), (1, 0), (0.5, 1), (0, 1)], color='yellow')
    generate_shape('star', num_points=8, inner_radius=0.2, outer_radius=1, color='purple')
    generate_shape('custom', path=[(0, 0), (1, 0.5), (0.5, 1), (0, 1)], color='orange') 
import matplotlib.pyplot as plt

def plot_triangle_over_line(line_start, line_end, triangle_height):
  """
  Plots a triangle above a given line segment.

  Args:
    line_start: A tuple representing the (x, y) coordinates of the line's starting point.
    line_end: A tuple representing the (x, y) coordinates of the line's ending point.
    triangle_height: The height of the triangle above the line.
  """

  fig, ax = plt.subplots()

  # Calculate midpoint of the line
  midpoint_x = (line_start[0] + line_end[0]) / 2
  midpoint_y = (line_start[1] + line_end[1]) / 2

  # Calculate direction vector of the line
  dx = line_end[0] - line_start[0]
  dy = line_end[1] - line_start[1]

  # Calculate perpendicular vector for triangle's peak
  perpendicular_x = -dy
  perpendicular_y = dx

  # Normalize perpendicular vector
  length = (perpendicular_x**2 + perpendicular_y**2)**0.5
  perpendicular_x /= length
  perpendicular_y /= length

  # Calculate peak coordinates
  peak_x = midpoint_x + perpendicular_x * triangle_height
  peak_y = midpoint_y + perpendicular_y * triangle_height

  # Define triangle coordinates
  triangle_coords = [line_start, line_end, (peak_x, peak_y)]

  # Create and plot the triangle
  triangle = plt.Polygon(triangle_coords, fill=True, edgecolor='black', facecolor='lightblue')
  ax.add_patch(triangle)

  # Plot the line
  plt.plot([line_start[0], line_end[0]], [line_start[1], line_end[1]], color='black')

  # Adjust plot limits and aspect ratio
  ax.autoscale()
  ax.set_aspect('equal')

  # Turn off axis
  ax.axis('off')

  # Show the plot
  plt.show()

# Example usage:
line_start = (0, 0)
line_end = (5, 2)
triangle_height = 2
plot_triangle_over_line(line_start, line_end, triangle_height)
# Call the test function to generate all shapes
test_generate_shape()
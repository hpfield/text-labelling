import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import glob
import seaborn as sns

POSSIBLE_TOPICS = 22 

# Function to compute false negatives given a DataFrame
def compute_false_negatives(df, thresh):
    gt = df['gt']
    scores = df['preds']

    predictions = scores.apply(lambda d: [k for k, v in d.items() if v >= thresh])

    false_negatives = []
    for gt_set, pred_set in zip(gt, predictions):
        false_negatives.extend(list(set(gt_set) - set(pred_set)))
    return false_negatives

def get_latest_file_path(data_path, chunk_size):
    pattern = os.path.join(data_path, f'cordis-telecoms-chunk_size-{chunk_size}_*.json')
    # print(f'Pattern: {pattern}')
    list_of_files = glob.glob(pattern)
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getmtime)
    return latest_file

def get_results(data_path):

    tel_topics = ["teleology","telecommunications","radio frequency","radar","mobile phones","bluetooth","WiFi","data networks","optical networks","microwave technology","radio technology","mobile radio","4G","LiFi","mobile network","radio and television","satellite radio","telecommunications networks","5G","fiber-optic network","cognitive radio","fixed wireless network",]

    results = []

    # Evaluate the performance of the LLM with each threshold from 0.1 to 1.0, incrementing by 0.1 each time
    for t in range(1, 11): 
        thresh = t / 10.0

        # Evaluate the ability of the model to predict topics with the current confidence threshold with all chunk sizes
        for chunk_size in range(1, POSSIBLE_TOPICS+1):
            file_path = get_latest_file_path(data_path, chunk_size)
            df = pd.read_json(file_path, lines=True)

            gt = df['gt']
            scores = df['preds']
            
            # Process predictions based on threshold
            predictions = scores.apply(lambda d: [k for k, v in d.items() if v >= thresh])

            # Compute metrics for each datapoint
            metrics_list = []
            for gt_set, pred_set in zip(gt, predictions):
                true_positives = len(set(gt_set) & set(pred_set))
                false_positives = len(set(pred_set) - set(gt_set))
                false_negatives = len(set(gt_set) - set(pred_set))
                true_negatives = len(set(tel_topics) - set(gt_set) - set(pred_set))

                accuracy = (true_positives + true_negatives) / (true_positives + false_positives + false_negatives + true_negatives)
                precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0
                recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0

                metrics_list.append((true_positives, false_positives, false_negatives, true_negatives, precision, recall, f1, accuracy))

            total_true_positives = sum(x[0] for x in metrics_list)
            total_false_positives = sum(x[1] for x in metrics_list)
            total_false_negatives = sum(x[2] for x in metrics_list)
            total_true_negatives = sum(x[3] for x in metrics_list)

            total_accuracy = sum(x[7] for x in metrics_list) / len(metrics_list)
            aggregated_precision = total_true_positives / (total_true_positives + total_false_positives) if (total_true_positives + total_false_positives) else 0
            aggregated_recall = total_true_positives / (total_true_positives + total_false_negatives) if (total_true_positives + total_false_negatives) else 0
            aggregated_f1 = 2 * (aggregated_precision * aggregated_recall) / (aggregated_precision + aggregated_recall) if (aggregated_precision + aggregated_recall) else 0

            row = [thresh, chunk_size, aggregated_precision, aggregated_recall, aggregated_f1, total_accuracy]
            results.append(row)

    results_df = pd.DataFrame(results, columns=['Threshold', 'Chunk Size', 'Precision', 'Recall', 'F1_score', 'Accuracy'])
    return results_df

def get_binary_results(data_path):


    results = []

    # Evaluate the performance of the LLM with each threshold from 0.1 to 1.0, incrementing by 0.1 each time
    for t in range(1, 11):
        thresh = t / 10.0

        # Evaluate the ability of the model to predict topics with the current confidence threshold with all chunk sizes
        file_path = data_path + f'cordis-telecoms-binary.json'
        df = pd.read_json(file_path, lines=True)

        gt = df['gt']
        scores = df['topics']

        # Process predictions based on threshold
        predictions = scores.apply(lambda d: [k for k, v in d.items() if v >= thresh])

        # Compute metrics for each datapoint
        metrics_list = []
        for gt_set, pred_set in zip(gt, predictions):
            true_positives = len(set(gt_set) & set(pred_set))
            false_positives = len(set(pred_set) - set(gt_set))
            false_negatives = len(set(gt_set) - set(pred_set))
            true_negatives = len(set(tel_topics) - set(gt_set) - set(pred_set))

            accuracy = (true_positives + true_negatives) / (true_positives + false_positives + false_negatives + true_negatives)
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0

            metrics_list.append((true_positives, false_positives, false_negatives, true_negatives, precision, recall, f1, accuracy))

        total_true_positives = sum(x[0] for x in metrics_list)
        total_false_positives = sum(x[1] for x in metrics_list)
        total_false_negatives = sum(x[2] for x in metrics_list)
        total_true_negatives = sum(x[3] for x in metrics_list)

        total_accuracy = sum(x[7] for x in metrics_list) / len(metrics_list)
        aggregated_precision = total_true_positives / (total_true_positives + total_false_positives) if (total_true_positives + total_false_positives) else 0
        aggregated_recall = total_true_positives / (total_true_positives + total_false_negatives) if (total_true_positives + total_false_negatives) else 0
        aggregated_f1 = 2 * (aggregated_precision * aggregated_recall) / (aggregated_precision + aggregated_recall) if (aggregated_precision + aggregated_recall) else 0

        row = [thresh, chunk_size, aggregated_precision, aggregated_recall, aggregated_f1, total_accuracy]
        results.append(row)

    results_df = pd.DataFrame(results, columns=['Threshold', 'Chunk Size', 'Precision', 'Recall', 'F1_score', 'Accuracy'])
    return results_df


def print_false_negatives(metrics, results_df, data_path):
    # Get best performance

    optimal_thresholds = {}

    for metric in metrics:
        # Find the optimal threshold for maximizing this metric
        optimal_row = results_df.loc[results_df[metric].idxmax()]
        optimal_threshold = optimal_row['Threshold']
        optimal_chunk_size = int(optimal_row['Chunk Size'])
        optimal_thresholds[metric] = (optimal_threshold, optimal_chunk_size)

        # Load the corresponding dataset and compute false negatives
        optimal_file_path = get_latest_file_path(data_path, optimal_chunk_size)
        df_optimal = pd.read_json(optimal_file_path, lines=True)
        false_negatives = compute_false_negatives(df_optimal, optimal_threshold)

        # Find the 5 most common false negatives
        most_common_fns = Counter(false_negatives).most_common(5)

        # Print the results for each metric
        print(f"Top 5 most common false negatives for {metric} (Optimal Threshold: {optimal_threshold}):")
        for label, count in most_common_fns:
            print(f"{label}: {count} occurrences")
        print()

def save_best(metrics, results_df, best_results_file):
    best_rows = []

    for metric in metrics:
        best_row = results_df.loc[results_df[metric].idxmax()] 
        best_rows.append({
            'Metric': metric,
            'Best Score': best_row[metric],
            'Threshold': best_row['Threshold'],
            'Chunk Size': best_row['Chunk Size']
        })

    best_df = pd.DataFrame(best_rows)

    best_df = best_df[['Metric', 'Best Score', 'Threshold', 'Chunk Size']]
    best_df.to_csv(best_results_file, index=False)

# def plot_metrics(metrics, results_df):
#     for metric in metrics:
#         fig = plt.figure()
#         ax = fig.add_subplot(111, projection='3d')
#         x = results_df['Threshold']
#         z = results_df['Chunk Size']
#         y = results_df[metric]

#         ax.scatter(x, z, y)
#         ax.set_xlabel('Threshold')
#         ax.set_ylabel('Chunk Size')
#         ax.set_zlabel(metric)
#         ax.set_title(f'3D Plot of {metric}')
#         plt.show()

import os
import plotly.graph_objects as go

def plot_metrics(metrics, results_df, save_dir):
    # Ensure the directory exists
    os.makedirs('plots', exist_ok=True)

    for metric in metrics:
        fig = go.Figure(data=[go.Scatter3d(
            x=results_df['Threshold'],
            y=results_df['Chunk Size'],
            z=results_df[metric],
            mode='markers',
            marker=dict(size=5)
        )])

        fig.update_layout(
            scene=dict(
                xaxis_title='Threshold',
                yaxis_title='Chunk Size',
                zaxis_title=metric,
                camera=dict(
                    eye=dict(x=1.25, y=1.25, z=1.25),  # Adjust to change the initial view
                    center=dict(x=0, y=0, z=-0.2),  # Adjust center to keep the plot centered
                ),
                aspectmode='manual',  # Allows manual resizing of the plot
                aspectratio=dict(x=1, y=1, z=0.7)  # Adjust to maintain proportions
            ),
            title=f'3D Plot of {metric}',
            width=800,  # Width of the plot in pixels
            height=800,  # Height of the plot in pixels
            margin=dict(l=0, r=0, t=0, b=0),
            autosize=False
        )
        # Save as a static image
        file_path = os.path.join(save_dir, f'{metric}_plot.')
        fig.write_image(file_path + 'png')
        fig.write_html(file_path + 'html')
        print(f"Plot saved as static image to {file_path}")
        # fig.show()

def plot_best_thresholds(best_results_file, save_dir):
    # Load the best results CSV file
    best_df = pd.read_csv(best_results_file)

    # Set up the plot
    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=best_df,
        x='Chunk Size',
        y='Threshold',
        hue='Metric',
        style='Metric',
        palette='deep',
        s=100
    )
    
    # Customize the plot
    plt.xlabel('Chunk Size')
    plt.ylabel('Best Threshold')
    plt.title('Best Confidence Threshold for Each Metric by Chunk Size')
    plt.grid(True)
    plt.legend(title='Metric', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Save the plot
    plot_path = os.path.join(save_dir, 'best_thresholds_scatter_plot.png')
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.show()
    print(f"Scatter plot saved to {plot_path}")

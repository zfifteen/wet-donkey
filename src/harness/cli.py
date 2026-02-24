# harness/cli.py
import argparse

def main():
    parser = argparse.ArgumentParser(description="Legacy OpenAI-compatible harness.")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--project-dir", required=True)
    
    args = parser.parse_args()
    
    print("This is the legacy harness.")
    print(f"Phase: {args.phase}")
    print(f"Project Dir: {args.project_dir}")
    print("This harness is a fallback and is not fully implemented.")

if __name__ == "__main__":
    main()

'use client';

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from 'lucide-react';
import axios from 'axios';
import './index.css';

export default function TitleVerificationForm() {
  const [title, setTitle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    verified: boolean;
    probability: number;
    reason: string;
    similar_titles?: string[];
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await axios.post('http://127.0.0.1:5000/verify', {
        title,
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error verifying title:', error);
      setResult({
        verified: false,
        probability: 0,
        reason: 'An error occurred while verifying the title. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-40">
      <div className="w-full max-w-lg mx-auto"> {/* Increased max-width */}
        <Card className="hover:shadow-lg transition-shadow p-6"> {/* Added padding */}
          <CardHeader>
            <CardTitle className="text-center text-lg font-semibold">
              Title Verification System
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6"> {/* Increased spacing */}
              <div className="space-y-3">
                <label
                  htmlFor="title"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Enter Title
                </label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter your title here"
                  disabled={isLoading}
                  className="py-4 text-lg" 
                />
              </div>
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 text-lg hover:bg-primary/90"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verifying
                  </>
                ) : (
                  'Verify Title'
                )}
              </Button>
            </form>
            {result && (
              <div className="mt-6 p-6 border rounded-md bg-blue"> {/* Increased padding */}
                <h3 className="font-semibold text-lg mb-4">
                  {result.verified ? 'Title Verified' : 'Verification Failed'}
                </h3>
                <p className="text-sm text-white mb-4">{result.reason}</p>
                <div className="flex items-center">
                  <div className="flex-grow bg-gray-200 rounded-full h-3 mr-3"> {/* Larger progress bar */}
                    <div
                      className={`h-3 rounded-full ${
                        result.verified ? 'bg-green-600' : 'bg-red-600'
                      }`}
                      style={{ width: `${result.probability * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    {(result.probability * 100).toFixed(1)}%
                  </span>
                </div>
                {result.similar_titles && result.similar_titles.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium mb-2">Similar Titles:</h4>
                    <ul className="list-disc pl-6">
                      {result.similar_titles.map((title, idx) => (
                        <li key={idx} className="text-sm text-gray-600">
                          {title}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

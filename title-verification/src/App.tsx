'use client';

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from 'lucide-react';
import axios from 'axios';

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
    <div className="flex items-center justify-center min-h-screen bg-gray-50 p-40">
      <div className="w-full max-w-md mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Title Verification System</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
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
                />
              </div>
              <Button type="submit" disabled={isLoading} className="w-full">
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
              <div className="mt-4 p-4 border rounded-md bg-gray-50">
                <h3 className="font-semibold text-lg mb-2">
                  {result.verified ? 'Title Verified' : 'Verification Failed'}
                </h3>
                <p className="text-sm text-gray-600 mb-2">{result.reason}</p>
                <div className="flex items-center">
                  <div className="flex-grow bg-gray-200 rounded-full h-2.5 mr-2">
                    <div
                      className={`h-2.5 rounded-full ${
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
                  <div className="mt-2">
                    <h4 className="text-sm font-medium mb-1">Similar Titles:</h4>
                    <ul className="list-disc pl-4">
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